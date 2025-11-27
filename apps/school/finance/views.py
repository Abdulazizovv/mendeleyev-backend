"""
Moliya tizimi views.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db.models import Q, Sum, Count
from django.db import models
from django.db.models.functions import TruncDate, TruncMonth
from datetime import datetime, timedelta
from uuid import UUID

from .models import (
    CashRegister,
    Transaction,
    StudentBalance,
    SubscriptionPlan,
    Discount,
    Payment,
    TransactionType,
    TransactionStatus,
)
from .serializers import (
    CashRegisterSerializer,
    TransactionSerializer,
    TransactionCreateSerializer,
    StudentBalanceSerializer,
    SubscriptionPlanSerializer,
    DiscountSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
)
from .permissions import CanManageFinance
from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile


class BaseFinanceView:
    """Asosiy moliya view mixin."""
    
    def _get_branch_id(self):
        """Branch ID ni olish."""
        # JWT claim
        if hasattr(self.request, "auth") and isinstance(self.request.auth, dict):
            br_claim = self.request.auth.get("br") or self.request.auth.get("branch_id")
            if br_claim:
                try:
                    return str(UUID(str(br_claim)))
                except:
                    pass
        
        # Header
        branch_id = self.request.META.get("HTTP_X_BRANCH_ID")
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        # Query param
        if hasattr(self.request, 'query_params'):
            branch_id = self.request.query_params.get("branch_id")
        else:
            branch_id = self.request.GET.get("branch_id")
        
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        return None


# ==================== Cash Register Views ====================

class CashRegisterListView(generics.ListCreateAPIView, BaseFinanceView):
    """Kassalar ro'yxati va yaratish."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = CashRegisterSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'balance', 'created_at']
    ordering = ['-created_at']
    
    @extend_schema(
        summary="Kassalar ro'yxati",
        description="Filial kassalari ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Qidirish'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tartiblash'),
        ],
    )
    def get_queryset(self):
        """Kassalar ro'yxatini olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return CashRegister.objects.none()
        
        return CashRegister.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('branch')
    
    def get_serializer_class(self):
        """Serializer klassini olish."""
        if self.request.method == 'POST':
            return CashRegisterSerializer
        return CashRegisterSerializer


class CashRegisterDetailView(generics.RetrieveUpdateDestroyAPIView, BaseFinanceView):
    """Kassa ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = CashRegisterSerializer
    
    def get_queryset(self):
        """Kassa queryset."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return CashRegister.objects.none()
        
        return CashRegister.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('branch')


# ==================== Transaction Views ====================

class TransactionListView(generics.ListCreateAPIView, BaseFinanceView):
    """Tranzaksiyalar ro'yxati va yaratish."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['description', 'reference_number']
    ordering_fields = ['amount', 'transaction_date', 'created_at']
    ordering = ['-transaction_date']
    
    @extend_schema(
        summary="Tranzaksiyalar ro'yxati",
        description="Filial tranzaksiyalari ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('transaction_type', OpenApiTypes.STR, description='Tranzaksiya turi'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Holat'),
            OpenApiParameter('cash_register', OpenApiTypes.UUID, description='Kassa ID'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Qidirish'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tartiblash'),
        ],
    )
    def get_queryset(self):
        """Tranzaksiyalar ro'yxatini olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Transaction.objects.none()
        
        queryset = Transaction.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'branch',
            'cash_register',
            'student_profile',
            'employee_membership',
            'employee_membership__user',
        )
        
        # Filterlar
        transaction_type = self.request.query_params.get('transaction_type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        cash_register_id = self.request.query_params.get('cash_register')
        if cash_register_id:
            queryset = queryset.filter(cash_register_id=cash_register_id)
        
        return queryset
    
    def get_serializer_class(self):
        """Serializer klassini olish."""
        if self.request.method == 'POST':
            return TransactionCreateSerializer
        return TransactionSerializer


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView, BaseFinanceView):
    """Tranzaksiya ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        """Tranzaksiya queryset."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Transaction.objects.none()
        
        return Transaction.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'branch',
            'cash_register',
            'student_profile',
            'employee_membership',
        )


# ==================== Student Balance Views ====================

class StudentBalanceListView(generics.ListAPIView, BaseFinanceView):
    """O'quvchi balanslari ro'yxati."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = StudentBalanceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['student_profile__personal_number', 'student_profile__user_branch__user__first_name']
    ordering_fields = ['balance', 'created_at']
    ordering = ['-balance']
    
    @extend_schema(
        summary="O'quvchi balanslari ro'yxati",
        description="Filial o'quvchilari balanslari ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Qidirish'),
        ],
    )
    def get_queryset(self):
        """O'quvchi balanslari ro'yxatini olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return StudentBalance.objects.none()
        
        return StudentBalance.objects.filter(
            student_profile__user_branch__branch_id=branch_id,
            student_profile__user_branch__role=BranchRole.STUDENT,
            deleted_at__isnull=True,
            student_profile__deleted_at__isnull=True,
        ).select_related(
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
        )


class StudentBalanceDetailView(generics.RetrieveAPIView, BaseFinanceView):
    """O'quvchi balansi ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = StudentBalanceSerializer
    
    def get_queryset(self):
        """O'quvchi balansi queryset."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return StudentBalance.objects.none()
        
        return StudentBalance.objects.filter(
            student_profile__user_branch__branch_id=branch_id,
            deleted_at__isnull=True,
        ).select_related('student_profile')


# ==================== Subscription Plan Views ====================

class SubscriptionPlanListView(generics.ListCreateAPIView, BaseFinanceView):
    """Abonement tariflari ro'yxati va yaratish."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = SubscriptionPlanSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'grade_level_min', 'grade_level_max', 'created_at']
    ordering = ['grade_level_min']
    
    @extend_schema(
        summary="Abonement tariflari ro'yxati",
        description="Filial abonement tariflari ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, description='Faol tariflar'),
        ],
    )
    def get_queryset(self):
        """Abonement tariflari ro'yxatini olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return SubscriptionPlan.objects.none()
        
        # Filialga tegishli tariflar va umumiy tariflar
        queryset = SubscriptionPlan.objects.filter(
            models.Q(branch_id=branch_id) | models.Q(branch__isnull=True),
            deleted_at__isnull=True
        ).select_related('branch')
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class SubscriptionPlanDetailView(generics.RetrieveUpdateDestroyAPIView, BaseFinanceView):
    """Abonement tarifi ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = SubscriptionPlanSerializer
    
    def get_queryset(self):
        """Abonement tarifi queryset."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return SubscriptionPlan.objects.none()
        
        # Filialga tegishli tariflar va umumiy tariflar
        return SubscriptionPlan.objects.filter(
            models.Q(branch_id=branch_id) | models.Q(branch__isnull=True),
            deleted_at__isnull=True
        ).select_related('branch')


# ==================== Discount Views ====================

class DiscountListView(generics.ListCreateAPIView, BaseFinanceView):
    """Chegirmalar ro'yxati va yaratish."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = DiscountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['amount', 'created_at']
    ordering = ['-created_at']
    
    @extend_schema(
        summary="Chegirmalar ro'yxati",
        description="Filial chegirmalari ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('is_active', OpenApiTypes.BOOL, description='Faol chegirmalar'),
        ],
    )
    def get_queryset(self):
        """Chegirmalar ro'yxatini olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Discount.objects.none()
        
        # Filialga tegishli chegirmalar va umumiy chegirmalar
        queryset = Discount.objects.filter(
            models.Q(branch_id=branch_id) | models.Q(branch__isnull=True),
            deleted_at__isnull=True
        ).select_related('branch')
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset


class DiscountDetailView(generics.RetrieveUpdateDestroyAPIView, BaseFinanceView):
    """Chegirma ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = DiscountSerializer
    
    def get_queryset(self):
        """Chegirma queryset."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Discount.objects.none()
        
        # Filialga tegishli chegirmalar va umumiy chegirmalar
        return Discount.objects.filter(
            models.Q(branch_id=branch_id) | models.Q(branch__isnull=True),
            deleted_at__isnull=True
        ).select_related('branch')


# ==================== Payment Views ====================

class PaymentListView(generics.ListCreateAPIView, BaseFinanceView):
    """To'lovlar ro'yxati va yaratish."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['student_profile__personal_number', 'notes']
    ordering_fields = ['final_amount', 'payment_date', 'created_at']
    ordering = ['-payment_date']
    
    @extend_schema(
        summary="To'lovlar ro'yxati",
        description="Filial to'lovlari ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('student_profile', OpenApiTypes.UUID, description='O\'quvchi ID'),
            OpenApiParameter('period_start', OpenApiTypes.DATE, description='Davr boshlanishi'),
            OpenApiParameter('period_end', OpenApiTypes.DATE, description='Davr tugashi'),
        ],
    )
    def get_queryset(self):
        """To'lovlar ro'yxatini olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Payment.objects.none()
        
        queryset = Payment.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'student_profile',
            'branch',
            'subscription_plan',
            'discount',
            'transaction',
        )
        
        student_profile_id = self.request.query_params.get('student_profile')
        if student_profile_id:
            queryset = queryset.filter(student_profile_id=student_profile_id)
        
        return queryset
    
    def get_serializer_class(self):
        """Serializer klassini olish."""
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer


class PaymentDetailView(generics.RetrieveAPIView, BaseFinanceView):
    """To'lov ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = PaymentSerializer
    
    def get_queryset(self):
        """To'lov queryset."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Payment.objects.none()
        
        return Payment.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'student_profile',
            'branch',
            'subscription_plan',
            'discount',
            'transaction',
        )


# ==================== Statistics Views ====================

class FinanceStatisticsView(generics.GenericAPIView, BaseFinanceView):
    """Moliya statistikasi."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    
    @extend_schema(
        summary="Moliya statistikasi",
        description="Filial moliya statistikasi",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('start_date', OpenApiTypes.DATE, description='Boshlanish sanasi'),
            OpenApiParameter('end_date', OpenApiTypes.DATE, description='Tugash sanasi'),
        ],
    )
    def get(self, request):
        """Statistikani olish."""
        branch_id = self._get_branch_id()
        if not branch_id:
            return Response(
                {"detail": "Filial ID talab qilinadi."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sana filtrlari
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Tranzaksiyalar
        transactions = Transaction.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True,
            status=TransactionStatus.COMPLETED,
        )
        
        if start_date:
            transactions = transactions.filter(transaction_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(transaction_date__lte=end_date)
        
        # Umumiy kirim va chiqim
        total_income = transactions.filter(
            transaction_type__in=[TransactionType.INCOME, TransactionType.PAYMENT]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_expense = transactions.filter(
            transaction_type__in=[TransactionType.EXPENSE, TransactionType.SALARY]
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Kassalar balansi
        cash_registers = CashRegister.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True,
            is_active=True,
        )
        total_cash_balance = cash_registers.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        # O'quvchi balanslari
        student_balances = StudentBalance.objects.filter(
            student_profile__user_branch__branch_id=branch_id,
            deleted_at__isnull=True,
        )
        total_student_balance = student_balances.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        # To'lovlar statistikasi
        payments = Payment.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True,
        )
        if start_date:
            payments = payments.filter(payment_date__gte=start_date)
        if end_date:
            payments = payments.filter(payment_date__lte=end_date)
        
        total_payments = payments.aggregate(total=Sum('final_amount'))['total'] or 0
        payments_count = payments.count()
        
        # Oylik statistika
        monthly_stats = transactions.annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            income=Sum('amount', filter=Q(transaction_type__in=[TransactionType.INCOME, TransactionType.PAYMENT])),
            expense=Sum('amount', filter=Q(transaction_type__in=[TransactionType.EXPENSE, TransactionType.SALARY])),
        ).order_by('month')
        
        return Response({
            'summary': {
                'total_income': total_income,
                'total_expense': total_expense,
                'net_balance': total_income - total_expense,
                'total_cash_balance': total_cash_balance,
                'total_student_balance': total_student_balance,
                'total_payments': total_payments,
                'payments_count': payments_count,
            },
            'monthly_stats': list(monthly_stats),
        })

