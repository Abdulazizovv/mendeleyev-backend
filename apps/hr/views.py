"""HR API views."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime

from apps.hr.models import StaffRole, StaffProfile, BalanceTransaction, SalaryPayment
from apps.hr.serializers import (
    StaffRoleSerializer, StaffRoleListSerializer,
    StaffProfileSerializer, StaffProfileListSerializer, StaffProfileCreateSerializer,
    BalanceTransactionSerializer, BalanceTransactionCreateSerializer,
    SalaryPaymentSerializer, SalaryPaymentBulkSerializer,
    SalaryReportSerializer
)
from apps.common.permissions import IsSuperAdmin, IsBranchAdmin


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
    
    list: Get all staff profiles
    retrieve: Get staff profile details
    create: Create new staff profile
    update: Update staff profile
    destroy: Soft delete staff profile
    salary: Update staff salary
    transactions: Get staff transactions
    create_transaction: Create new transaction
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['branch', 'staff_role', 'employment_type', 'status']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'tax_id', 'bank_account'
    ]
    ordering_fields = ['hire_date', 'base_salary', 'current_balance', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get staff profiles with related data."""
        qs = StaffProfile.objects.filter(deleted_at__isnull=True)
        
        # Filter by branch if provided
        branch_id = self.request.query_params.get('branch')
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('active')
        if is_active is not None:
            qs = qs.filter(status='active' if is_active == 'true' else Q(~Q(status='active')))
        
        return qs.select_related('user', 'branch', 'staff_role', 'membership')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StaffProfileListSerializer
        elif self.action == 'create':
            return StaffProfileCreateSerializer
        return StaffProfileSerializer
    
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
