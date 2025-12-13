"""HR API views."""

import re
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.db import transaction, models
from datetime import datetime
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from apps.hr.models import StaffRole, StaffProfile, BalanceTransaction, SalaryPayment
from apps.hr.serializers import (
    StaffRoleSerializer, StaffRoleListSerializer,
    StaffProfileSerializer, StaffProfileListSerializer, StaffProfileCreateSerializer,
    BalanceTransactionSerializer, BalanceTransactionCreateSerializer,
    SalaryPaymentSerializer, SalaryPaymentBulkSerializer,
    SalaryReportSerializer, UserCheckSerializer
)
from apps.common.permissions import IsSuperAdmin, IsBranchAdmin
from auth.users.models import User
from apps.branch.models import BranchMembership


class StaffRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StaffRole management.
    
    list: Get all roles for current branch
    retrieve: Get role details
    create: Create new role (branch admin only)
    update: Update role (branch admin only)
    destroy: Soft delete role (branch admin only)
    permissions: Get role permissions
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['branch', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter by branch from query params or user's active branch."""
        qs = StaffRole.objects.filter(deleted_at__isnull=True)
        
        # Filter by branch if provided
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        
        return qs.select_related('branch')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StaffRoleListSerializer
        return StaffRoleSerializer
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Get role permissions."""
        role = self.get_object()
        return Response({
            'id': role.id,
            'name': role.name,
            'permissions': role.permissions
        })


class StaffProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StaffProfile management.
    
    list: Get all staff profiles with enhanced information
    retrieve: Get staff profile details
    create: Create new staff profile (use StaffCreateView for enhanced creation)
    update: Update staff profile
    destroy: Soft delete staff profile
    salary: Update staff salary
    transactions: Get staff transactions
    create_transaction: Create new transaction
    stats: Get staff statistics
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['branch', 'staff_role', 'employment_type', 'status']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'tax_id', 'bank_account', 'staff_role__name'
    ]
    ordering_fields = [
        'hire_date', 'base_salary', 'current_balance', 'created_at',
        'user__first_name', 'staff_role__name', 'branch__name'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get staff profiles with optimized queries."""
        qs = StaffProfile.objects.filter(deleted_at__isnull=True)
        
        # Filter by branch if provided
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('active')
        if is_active is not None:
            qs = qs.filter(status='active' if is_active == 'true' else Q(~Q(status='active')))
        
        # Filter by balance status
        balance_status = self.request.query_params.get('balance_status')
        if balance_status == 'positive':
            qs = qs.filter(current_balance__gt=0)
        elif balance_status == 'negative':
            qs = qs.filter(current_balance__lt=0)
        elif balance_status == 'zero':
            qs = qs.filter(current_balance=0)
        
        # Filter by hire date range
        hire_date_from = self.request.query_params.get('hire_date_from')
        hire_date_to = self.request.query_params.get('hire_date_to')
        if hire_date_from:
            qs = qs.filter(hire_date__gte=hire_date_from)
        if hire_date_to:
            qs = qs.filter(hire_date__lte=hire_date_to)
        
        # Optimize with select_related and prefetch_related
        return qs.select_related(
            'user', 'branch', 'staff_role', 'membership'
        ).prefetch_related(
            'balance_transactions'
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StaffProfileListSerializer
        return StaffProfileSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get staff statistics."""
        qs = self.filter_queryset(self.get_queryset())
        
        from django.db.models import Avg, Sum, Count, Q
        
        stats = qs.aggregate(
            total_count=Count('id'),
            active_count=Count('id', filter=Q(status='active')),
            inactive_count=Count('id', filter=Q(status__in=['inactive', 'terminated'])),
            total_salary=Sum('base_salary'),
            avg_salary=Avg('base_salary'),
            total_balance=Sum('current_balance'),
            positive_balance_count=Count('id', filter=Q(current_balance__gt=0)),
            negative_balance_count=Count('id', filter=Q(current_balance__lt=0)),
        )
        
        # By employment type
        by_employment = list(qs.values('employment_type').annotate(
            count=Count('id'),
            total_salary=Sum('base_salary')
        ).order_by('-count'))
        
        # By role
        by_role = list(qs.values(
            'staff_role__name', 'staff_role__id'
        ).annotate(
            count=Count('id'),
            avg_salary=Avg('base_salary')
        ).order_by('-count'))
        
        # By branch
        by_branch = list(qs.values(
            'branch__name', 'branch__id'
        ).annotate(
            count=Count('id'),
            total_salary=Sum('base_salary')
        ).order_by('-count'))
        
        return Response({
            'summary': stats,
            'by_employment_type': by_employment,
            'by_role': by_role,
            'by_branch': by_branch
        })


class StaffCreateView(views.APIView):
    """
    Enhanced API view for creating staff with comprehensive validation.
    Creates User, BranchMembership, and StaffProfile atomically.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = StaffProfileCreateSerializer
    
    @extend_schema(
        summary="Yangi xodim qo'shish",
        description="""
        Yangi xodim qo'shish uchun API endpoint.
        
        Bu endpoint quyidagi amallarni atomik tarzda bajaradi:
        1. User yaratish yoki mavjud userni topish (telefon raqam bo'yicha)
        2. BranchMembership yaratish yoki olish
        3. StaffProfile yaratish
        
        **Validatsiyalar:**
        - Telefon raqam formati (+998901234567)
        - Filial va rol mavjudligi va faolligi
        - Rol filialgа tegishli ekanligi
        - Maosh rolning diapazonida ekanligi
        - User allaqachon shu filialda xodim emasligini tekshirish
        
        **Qo'shimcha xususiyatlar:**
        - Agar user allaqachon mavjud bo'lsa, faqat yangilash (override emas)
        - Parol ixtiyoriy (berilmasa unusable password o'rnatiladi)
        - Soft-deleted membership'larni avtomatik tiklash
        """,
        request=StaffProfileCreateSerializer,
        responses={
            201: StaffProfileSerializer,
            400: OpenApiExample(
                'Validation Error',
                value={
                    "phone_number": ["Telefon raqam noto'g'ri formatda."],
                    "staff_role_id": ["Bu rol boshqa filialga tegishli."],
                    "base_salary": ["Maosh minimal qiymatdan kam bo'lishi mumkin emas."]
                },
                response_only=True,
            )
        },
        examples=[
            OpenApiExample(
                'Minimal ma\'lumotlar bilan',
                value={
                    "phone_number": "+998901234567",
                    "first_name": "Alisher",
                    "last_name": "Navoiy",
                    "branch_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "staff_role_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "employment_type": "full_time",
                    "hire_date": "2025-01-15",
                    "base_salary": 5000000
                },
                request_only=True,
            ),
            OpenApiExample(
                'To\'liq ma\'lumotlar bilan',
                value={
                    "phone_number": "+998901234567",
                    "first_name": "Alisher",
                    "last_name": "Navoiy",
                    "email": "alisher@example.com",
                    "password": "SecurePass123!",
                    "branch_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "staff_role_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "employment_type": "full_time",
                    "hire_date": "2025-01-15",
                    "base_salary": 5000000,
                    "bank_account": "1234567890123456",
                    "tax_id": "123456789",
                    "notes": "O'qituvchi, matematika"
                },
                request_only=True,
            ),
        ]
    )
    @transaction.atomic
    def post(self, request):
        """Yangi xodim yaratish."""
        serializer = StaffProfileCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        staff_profile = serializer.save()
        
        # Response serializer
        response_serializer = StaffProfileSerializer(staff_profile)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['patch'])
    def salary(self, request, pk=None):
        """Update staff salary."""
        staff = self.get_object()
        new_salary = request.data.get('base_salary')
        
        if not new_salary or new_salary < 0:
            return Response(
                {'error': 'base_salary maydoni to\'ldirilishi va musbat bo\'lishi kerak.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check salary range if role has one
        role = staff.staff_role
        if role.salary_range_min and new_salary < role.salary_range_min:
            return Response(
                {'error': f'Maosh minimal qiymatdan ({role.salary_range_min:,}) kam bo\'lishi mumkin emas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if role.salary_range_max and new_salary > role.salary_range_max:
            return Response(
                {'error': f'Maosh maksimal qiymatdan ({role.salary_range_max:,}) ko\'p bo\'lishi mumkin emas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_salary = staff.base_salary
        staff.base_salary = new_salary
        staff.save(update_fields=['base_salary', 'updated_at'])
        
        return Response({
            'message': 'Maosh muvaffaqiyatli yangilandi.',
            'old_salary': old_salary,
            'new_salary': new_salary
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get staff transactions."""
        staff = self.get_object()
        transactions = staff.balance_transactions.filter(
            deleted_at__isnull=True
        ).order_by('-created_at')
        
        # Pagination
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = BalanceTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = BalanceTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def create_transaction(self, request, pk=None):
        """Create new balance transaction."""
        staff = self.get_object()
        
        serializer = BalanceTransactionCreateSerializer(
            data=request.data,
            context={'staff': staff, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save()
        
        return Response(
            BalanceTransactionSerializer(transaction).data,
            status=status.HTTP_201_CREATED
        )


class BalanceTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for BalanceTransaction (read-only).
    
    Transactions are created via StaffProfile.create_transaction or automatically.
    """
    
    serializer_class = BalanceTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['staff', 'transaction_type', 'staff__branch']
    search_fields = ['reference', 'description', 'staff__user__first_name', 'staff__user__last_name']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get transactions with related data."""
        qs = BalanceTransaction.objects.filter(deleted_at__isnull=True)
        
        # Filter by branch if provided
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(staff__branch_id=branch_id)
        
        return qs.select_related('staff__user', 'staff__branch', 'processed_by')


class SalaryPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SalaryPayment management.
    
    list: Get all salary payments
    retrieve: Get salary payment details
    create: Create new salary payment
    update: Update salary payment
    destroy: Soft delete salary payment
    bulk: Bulk create salary payments
    report: Get salary report for a month
    """
    
    serializer_class = SalaryPaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['staff', 'status', 'payment_method', 'staff__branch']
    search_fields = ['staff__user__first_name', 'staff__user__last_name', 'reference_number']
    ordering_fields = ['payment_date', 'amount', 'created_at']
    ordering = ['-payment_date']
    
    def get_queryset(self):
        """Get salary payments with related data."""
        qs = SalaryPayment.objects.filter(deleted_at__isnull=True)
        
        # Filter by branch if provided
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(staff__branch_id=branch_id)
        
        # Filter by month if provided
        month = self.request.query_params.get('month')
        if month:
            try:
                month_date = datetime.strptime(month, '%Y-%m-%d').date()
                qs = qs.filter(month=month_date)
            except ValueError:
                pass
        
        return qs.select_related('staff__user', 'staff__branch', 'processed_by')
    
    def perform_create(self, serializer):
        """Set processed_by on create."""
        serializer.save(processed_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def bulk(self, request):
        """
        Bulk create salary payments.
        
        Expected payload:
        {
            "month": "2024-01-01",
            "payments": [
                {"staff_id": 1, "amount": 5000000, "payment_date": "2024-01-05", "payment_method": "cash", "notes": ""},
                ...
            ]
        }
        
        This endpoint queues a Celery task for processing.
        """
        from apps.hr.tasks import process_bulk_salary_payments
        
        month = request.data.get('month')
        payments = request.data.get('payments', [])
        
        if not month:
            return Response(
                {'error': 'month maydoni to\'ldirilishi kerak.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not payments:
            return Response(
                {'error': 'payments ro\'yxati bo\'sh bo\'lishi mumkin emas.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate each payment
        serializer = SalaryPaymentBulkSerializer(data=payments, many=True)
        serializer.is_valid(raise_exception=True)
        
        # Queue task
        task = process_bulk_salary_payments.delay(
            month=month,
            payments=serializer.validated_data,
            processed_by_id=str(request.user.id)
        )
        
        return Response({
            'message': 'Maosh to\'lovlari navbatga qo\'shildi.',
            'task_id': task.id,
            'total_payments': len(payments)
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'], url_path='report/(?P<month>[^/.]+)')
    def report(self, request, month=None):
        """
        Get salary report for a specific month.
        
        URL: /api/hr/salaries/report/2024-01-01/
        """
        try:
            month_date = datetime.strptime(month, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Noto\'g\'ri oy formati. Misol: 2024-01-01'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        branch_id = request.query_params.get('branch')
        qs = SalaryPayment.objects.filter(
            month=month_date,
            deleted_at__isnull=True
        )
        
        if branch_id:
            qs = qs.filter(staff__branch_id=branch_id)
        
        # Aggregate data
        total_stats = qs.aggregate(
            total_staff=Count('staff', distinct=True),
            total_paid=Count('id', filter=Q(status='paid')),
            total_amount=Sum('amount', filter=Q(status='paid')) or 0
        )
        
        # By role
        by_role = list(qs.values(
            'staff__staff_role__name'
        ).annotate(
            count=Count('id'),
            total=Sum('amount', filter=Q(status='paid')) or 0
        ).order_by('-total'))
        
        # By status
        by_status = dict(qs.values_list('status').annotate(Count('id')))
        
        data = {
            'month': month_date,
            'total_staff': total_stats['total_staff'],
            'total_paid': total_stats['total_paid'],
            'total_amount': total_stats['total_amount'],
            'by_role': by_role,
            'by_status': by_status
        }
        
        serializer = SalaryReportSerializer(data)
        return Response(serializer.data)


class PhoneLookupMixin:
    """Telefon raqam bilan qidirish uchun umumiy mixin."""
    
    lookup_serializer_class = UserCheckSerializer
    permission_classes = [IsAuthenticated]

    def _get_payload(self, request):
        data = request.query_params if request.method == 'GET' else request.data
        serializer = self.lookup_serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _normalize_phone_variants(self, phone_number: str) -> list[str]:
        """Telefon raqamni bir nechta variantga normalizatsiya qilish."""
        raw = re.sub(r'\s+', '', str(phone_number or ''))
        variants = {raw}
        if raw.startswith('+'):
            variants.add(raw[1:])
        else:
            variants.add(f'+{raw}')
        return [variant for variant in variants if variant]

    def _build_phone_query(self, variants):
        """Variantlar bo'yicha Q obyektini yaratish."""
        query = models.Q()
        for variant in variants:
            query |= models.Q(phone_number=variant)
        return query


class StaffCheckView(PhoneLookupMixin, views.APIView):
    """Telefon raqam orqali xodim mavjudligini tekshirish.
    
    Avval berilgan filialda qidiradi, agar topilmasa barcha filiallarda qidiradi.
    """

    @extend_schema(
        summary="Xodim mavjudligini tekshirish",
        description="""
        Telefon raqam orqali xodim mavjudligini tekshirish.
        
        Query/body parameters:
        - phone_number (required): Telefon raqami
        - branch_id (optional): Filial ID (agar berilmasa, barcha filiallarda qidiriladi)
        
        Response ma'lumotlari:
        - exists_in_branch: Berilgan filialda xodim mavjudmi
        - exists_globally: Istalgan filialda xodim mavjudmi
        - branch_data: Berilgan filialdagi xodim ma'lumotlari
        - all_branches_data: Barcha filiallardagi xodim ma'lumotlari
        """,
        parameters=[
            OpenApiParameter(
                'phone_number',
                OpenApiTypes.STR,
                description='Telefon raqami (+998901234567)',
                required=True
            ),
            OpenApiParameter(
                'branch_id',
                OpenApiTypes.UUID,
                description='Filial ID (ixtiyoriy)',
                required=False
            ),
        ],
        examples=[
            OpenApiExample(
                'Telefon tekshirish',
                value={
                    'phone_number': '+998901234567',
                    'branch_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6'
                },
                request_only=True,
            ),
        ]
    )
    def get(self, request):
        return self._handle(request)
    
    def post(self, request):
        return self._handle(request)
    
    def _handle(self, request):
        params = self._get_payload(request)
        branch_id = str(params.get('branch_id') or '') or None
        phone_variants = self._normalize_phone_variants(params['phone_number'])
        
        if not phone_variants:
            return Response(
                {"detail": "Telefon raqam noto'g'ri formatda."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.filter(self._build_phone_query(phone_variants)).first()
        if not user:
            return Response({
                "exists_in_branch": False,
                "exists_globally": False,
                "branch_data": None,
                "all_branches_data": [],
            })
        
        # Xodim profillarini olish
        staff_profiles = StaffProfile.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).select_related(
            'branch',
            'staff_role',
            'membership',
            'user'
        )
        
        all_branches_data = []
        branch_data = None
        
        for profile in staff_profiles:
            data = {
                'branch_id': str(profile.branch.id),
                'branch_name': profile.branch.name,
                'is_active': profile.membership.is_active if profile.membership else False,
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'user': {
                    'id': str(profile.user.id),
                    'phone_number': profile.user.phone_number,
                    'first_name': profile.user.first_name,
                    'last_name': profile.user.last_name,
                    'full_name': profile.user.get_full_name(),
                },
                'staff_profile': {
                    'id': str(profile.id),
                    'staff_role': {
                        'id': str(profile.staff_role.id),
                        'name': profile.staff_role.name,
                        'code': profile.staff_role.code,
                    },
                    'employment_type': profile.employment_type,
                    'employment_type_display': profile.get_employment_type_display(),
                    'base_salary': profile.base_salary,
                    'current_balance': profile.current_balance,
                    'status': profile.status,
                    'status_display': profile.get_status_display(),
                    'hire_date': profile.hire_date.isoformat() if profile.hire_date else None,
                    'termination_date': profile.termination_date.isoformat() if profile.termination_date else None,
                }
            }
            
            all_branches_data.append(data)
            
            if branch_id and data['branch_id'] == branch_id:
                branch_data = data
        
        return Response({
            "exists_in_branch": branch_data is not None,
            "exists_globally": bool(all_branches_data),
            "branch_data": branch_data,
            "all_branches_data": all_branches_data,
        })
