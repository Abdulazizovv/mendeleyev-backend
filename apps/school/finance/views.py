"""
Moliya tizimi views.
"""
from rest_framework import generics, status, serializers
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
    StudentSubscription,
    TransactionType,
    TransactionStatus,
    FinanceCategory,
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
    StudentSubscriptionSerializer,
    StudentSubscriptionCreateSerializer,
    PaymentDueSummarySerializer,
    FinanceCategorySerializer,
    FinanceCategoryListSerializer,
)
from .permissions import CanManageFinance
from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile


class BaseFinanceView:
    """Asosiy moliya view mixin."""
    
    def _get_branch_id(self):
        """
        Branch ID ni olish.
        
        Middleware request.branch_id o'rnatadi.
        Fallback sifatida manual extraction.
        """
        # Middleware dan
        if hasattr(self.request, 'branch_id') and self.request.branch_id:
            return self.request.branch_id
        
        # Fallback: manual extraction
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
        
        # User membership dan olish
        try:
            membership = BranchMembership.objects.filter(
                user=self.request.user,
                deleted_at__isnull=True
            ).first()
            if membership and membership.branch_id:
                return str(membership.branch_id)
        except Exception:
            pass
        
        return None
    
    def _is_super_admin(self):
        """Super admin ekanligini tekshirish."""
        # Middleware dan
        if hasattr(self.request, 'is_super_admin'):
            return self.request.is_super_admin
        
        # Fallback: manual check
        if self.request.user.is_superuser:
            return True
        
        try:
            membership = BranchMembership.objects.filter(
                user=self.request.user,
                deleted_at__isnull=True
            ).first()
            return membership and membership.role == BranchRole.SUPER_ADMIN
        except Exception:
            return False
    
    def _should_auto_approve(self):
        """Tranzaksiya avtomatik tasdiqlanishi kerakligini aniqlash."""
        # Super admin - manual tasdiq talab qilinadi
        if self._is_super_admin():
            return False
        
        # Branch admin - avtomatik tasdiqlanadi
        try:
            membership = BranchMembership.objects.filter(
                user=self.request.user,
                deleted_at__isnull=True
            ).first()
            if membership and membership.role == BranchRole.BRANCH_ADMIN:
                return True
        except Exception:
            pass
        
        # Boshqa rollar - manual tasdiq
        return False


# ==================== Finance Category Views ====================

@extend_schema(tags=['Finance Categories'])
class FinanceCategoryListCreateView(BaseFinanceView, generics.ListCreateAPIView):
    """Kategoriyalar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type', 'is_active', 'parent']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['type', 'name']
    
    def get_queryset(self):
        """QuerySet ni olish."""
        queryset = FinanceCategory.objects.select_related('branch', 'parent')
        
        # Super admin barcha kategoriyalarni ko'radi
        if self._is_super_admin():
            return queryset
        
        # Oddiy foydalanuvchilar: global + o'z filiali kategoriyalari
        branch_id = self._get_branch_id()
        if branch_id:
            queryset = queryset.filter(
                Q(branch__isnull=True) | Q(branch_id=branch_id)
            )
        else:
            queryset = queryset.filter(branch__isnull=True)
        
        return queryset
    
    def get_serializer_class(self):
        """Serializer tanlash."""
        if self.request.method == 'GET':
            return FinanceCategoryListSerializer
        return FinanceCategorySerializer
    
    def perform_create(self, serializer):
        """Kategoriya yaratish."""
        # Agar branch berilmagan bo'lsa, requestdan olish
        if 'branch' not in serializer.validated_data or serializer.validated_data.get('branch') is None:
            # Super admin global kategoriya yaratishi mumkin
            if self._is_super_admin():
                # Super admin uchun: branch berilmasa, global kategoriya
                serializer.save()  # branch=None (global)
            else:
                # Oddiy foydalanuvchilar uchun: DOIM filial kategoriya
                branch_id = self._get_branch_id()
                if not branch_id:
                    raise serializers.ValidationError({
                        'branch': 'Branch ID topilmadi. Iltimos X-Branch-Id headerni yuboring.'
                    })
                serializer.save(branch_id=branch_id)
        else:
            # Branch aniq berilgan
            serializer.save()


@extend_schema(tags=['Finance Categories'])
class FinanceCategoryDetailView(BaseFinanceView, generics.RetrieveUpdateDestroyAPIView):
    """Kategoriya detali, o'zgartirish va o'chirish."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = FinanceCategorySerializer
    
    def get_queryset(self):
        """QuerySet ni olish."""
        queryset = FinanceCategory.objects.select_related('branch', 'parent')
        
        # Super admin barcha kategoriyalarni ko'radi
        if self._is_super_admin():
            return queryset
        
        # Oddiy foydalanuvchilar: global + o'z filiali kategoriyalari
        branch_id = self._get_branch_id()
        if branch_id:
            pass
        
        # Oddiy foydalanuvchilar: global + o'z filiali kategoriyalari
        if branch_id:
            queryset = queryset.filter(
                Q(branch__isnull=True) | Q(branch_id=branch_id)
            )
        else:
            queryset = queryset.filter(branch__isnull=True)
        
        return queryset


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
        return CashRegisterSerializer
    
    def perform_create(self, serializer):
        """Kassa yaratish."""
        # Agar branch berilmagan bo'lsa, requestdan olish
        if 'branch' not in serializer.validated_data or serializer.validated_data.get('branch') is None:
            branch_id = self._get_branch_id()
            if not branch_id:
                raise serializers.ValidationError({
                    'branch': 'Branch ID topilmadi. Iltimos X-Branch-Id headerni yuboring.'
                })
            serializer.save(branch_id=branch_id)
        else:
            serializer.save()


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
            OpenApiParameter('category', OpenApiTypes.UUID, description='Kategoriya ID'),
            OpenApiParameter('student_profile', OpenApiTypes.UUID, description='O\'quvchi ID'),
            OpenApiParameter('employee_membership', OpenApiTypes.UUID, description='Xodim membership ID'),
            OpenApiParameter('date_from', OpenApiTypes.DATE, description='Boshlanish sanasi (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.DATE, description='Tugash sanasi (YYYY-MM-DD)'),
            OpenApiParameter('payment_method', OpenApiTypes.STR, description='To\'lov usuli'),
            OpenApiParameter('search', OpenApiTypes.STR, description='Qidirish'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tartiblash'),
        ],
    )
    def get_queryset(self):
        """Tranzaksiyalar ro'yxatini olish."""
        queryset = Transaction.objects.select_related(
            'branch',
            'cash_register',
            'category',
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
            'employee_membership',
            'employee_membership__user',
            'employee_membership__user__profile',
        )
        
        # Super admin barcha tranzaksiyalarni ko'radi
        if not self._is_super_admin():
            branch_id = self._get_branch_id()
            if not branch_id:
                return Transaction.objects.none()
            queryset = queryset.filter(branch_id=branch_id)
        
        # Soft delete filtri
        queryset = queryset.filter(deleted_at__isnull=True)
        
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
        
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Student filter
        student_profile_id = self.request.query_params.get('student_profile')
        if student_profile_id:
            queryset = queryset.filter(student_profile_id=student_profile_id)
        
        # Employee filter
        employee_membership_id = self.request.query_params.get('employee_membership')
        if employee_membership_id:
            queryset = queryset.filter(employee_membership_id=employee_membership_id)
        
        # Payment method filter
        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        
        # Date range filter
        date_from = self.request.query_params.get('date_from')
        if date_from:
            from datetime import datetime
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(transaction_date__gte=date_from_obj)
            except ValueError:
                pass
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            from datetime import datetime, timedelta
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(transaction_date__lt=date_to_obj)
            except ValueError:
                pass
        
        return queryset
    
    def get_serializer_class(self):
        """Serializer klassini olish."""
        if self.request.method == 'POST':
            return TransactionCreateSerializer
        return TransactionSerializer
    
    def perform_create(self, serializer):
        """Tranzaksiya yaratish."""
        # Agar branch berilmagan bo'lsa, requestdan olish
        if 'branch' not in serializer.validated_data or serializer.validated_data.get('branch') is None:
            branch_id = self._get_branch_id()
            if not branch_id:
                raise serializers.ValidationError({
                    'branch': 'Branch ID topilmadi. Iltimos X-Branch-Id headerni yuboring.'
                })
            # User role asosida status aniqlash
            auto_approve = self._should_auto_approve()
            serializer.save(branch_id=branch_id, auto_approve=auto_approve)
        else:
            auto_approve = self._should_auto_approve()
            serializer.save(auto_approve=auto_approve)
    
    def create(self, request, *args, **kwargs):
        """Tranzaksiya yaratish va to'liq ma'lumot qaytarish."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Response uchun TransactionSerializer ishlatish
        instance = serializer.instance
        response_serializer = TransactionSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView, BaseFinanceView):
    """Tranzaksiya ma'lumotlari."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        """Tranzaksiya queryset."""
        queryset = Transaction.objects.select_related(
            'branch',
            'cash_register',
            'category',
            'student_profile',
            'employee_membership',
        )
        
        # Super admin barcha tranzaksiyalarni ko'radi
        if not self._is_super_admin():
            branch_id = self._get_branch_id()
            if not branch_id:
                return Transaction.objects.none()
            queryset = queryset.filter(branch_id=branch_id)
        
        return queryset.filter(deleted_at__isnull=True)


# ==================== Student Balance Views ====================



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
    
    def perform_create(self, serializer):
        """Abonement tarifi yaratish."""
        # Agar branch berilmagan bo'lsa, requestdan olish
        if 'branch' not in serializer.validated_data:
            branch_id = self._get_branch_id()
            if branch_id:
                serializer.save(branch_id=branch_id)
            else:
                # Super admin global tarif yaratishi mumkin
                if self._is_super_admin():
                    serializer.save()  # Global tarif
                else:
                    raise serializers.ValidationError({
                        'branch': 'Branch ID talab qilinadi'
                    })
        else:
            serializer.save()


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
    
    def perform_create(self, serializer):
        """Chegirma yaratish."""
        # Agar branch berilmagan bo'lsa, requestdan olish
        if 'branch' not in serializer.validated_data:
            branch_id = self._get_branch_id()
            if branch_id:
                serializer.save(branch_id=branch_id)
            else:
                # Super admin global chegirma yaratishi mumkin
                if self._is_super_admin():
                    serializer.save()  # Global chegirma
                else:
                    raise serializers.ValidationError({
                        'branch': 'Branch ID talab qilinadi'
                    })
        else:
            serializer.save()


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
            'student_profile__user_branch__user',
            'student_profile__user_branch__user__profile',
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
    
    def perform_create(self, serializer):
        """To'lov yaratish."""
        # Agar branch berilmagan bo'lsa, requestdan olish
        if 'branch' not in serializer.validated_data or serializer.validated_data.get('branch') is None:
            branch_id = self._get_branch_id()
            if not branch_id:
                raise serializers.ValidationError({
                    'branch': 'Branch ID topilmadi. Iltimos X-Branch-Id headerni yuboring.'
                })
            serializer.save(branch_id=branch_id)
        else:
            serializer.save()


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


class StudentSubscriptionListView(BaseFinanceView, generics.ListCreateAPIView):
    """O'quvchi abonementlari ro'yxati va yaratish API."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['student_profile', 'subscription_plan', 'is_active']
    search_fields = ['student_profile__user_branch__user__first_name', 'student_profile__user_branch__user__last_name']
    ordering_fields = ['created_at', 'next_payment_date', 'total_debt']
    ordering = ['-created_at']
    
    def get_queryset(self):
        branch_id = self._get_branch_id()
        return StudentSubscription.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
            'subscription_plan',
            'branch'
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentSubscriptionCreateSerializer
        return StudentSubscriptionSerializer
    
    @extend_schema(
        summary="O'quvchi abonementlari ro'yxati",
        description="O'quvchi abonementlarini ro'yxatini olish. Branch ID header orqali berilishi kerak.",
        parameters=[
            OpenApiParameter(name='student_profile', type=OpenApiTypes.UUID, description='O\'quvchi profili ID'),
            OpenApiParameter(name='subscription_plan', type=OpenApiTypes.UUID, description='Abonement tarifi ID'),
            OpenApiParameter(name='is_active', type=OpenApiTypes.BOOL, description='Faol abonementlar'),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchi abonementi yaratish",
        description="O'quvchi uchun yangi abonement yaratish."
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class StudentSubscriptionDetailView(BaseFinanceView, generics.RetrieveUpdateDestroyAPIView):
    """O'quvchi abonementi detail API."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = StudentSubscriptionSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        branch_id = self._get_branch_id()
        return StudentSubscription.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
            'subscription_plan',
            'branch'
        )
    
    @extend_schema(
        summary="O'quvchi abonementi tafsilotlari",
        description="O'quvchi abonementi to'liq ma'lumotlarini olish."
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchi abonementini yangilash",
        description="O'quvchi abonementi ma'lumotlarini yangilash."
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchi abonementini o'chirish",
        description="O'quvchi abonementini o'chirish (soft delete)."
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class PaymentDueSummaryView(BaseFinanceView, generics.GenericAPIView):
    """O'quvchi to'lov xulosa API.
    
    O'quvchi qancha to'lashi kerakligini ko'rsatadi.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentDueSummarySerializer
    
    @extend_schema(
        summary="O'quvchi to'lov xulosa",
        description="""
        O'quvchi qancha to'lashi kerakligini ko'rsatadi.
        
        Qaytariladi:
        - Joriy davr uchun summa
        - Qarz summasi
        - Jami to'lanishi kerak
        - Keyingi to'lov sanasi
        - Kechikkan oylar soni
        
        Query parametrlar:
        - student_profile_id: O'quvchi profili ID (UUID)
        """,
        parameters=[
            OpenApiParameter(
                name='student_profile_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                required=True,
                description='O\'quvchi profili ID'
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """O'quvchi to'lov xulosasini olish."""
        from datetime import date
        
        branch_id = self._get_branch_id()
        student_profile_id = request.query_params.get('student_profile_id')
        
        if not student_profile_id:
            return Response(
                {'error': 'student_profile_id parametri talab qilinadi'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student_profile = StudentProfile.objects.get(id=student_profile_id)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'O\'quvchi profili topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # O'quvchining faol abonementlarini olish
        subscriptions = StudentSubscription.objects.filter(
            student_profile=student_profile,
            branch_id=branch_id,
            is_active=True,
            deleted_at__isnull=True
        ).select_related('subscription_plan')
        
        if not subscriptions.exists():
            return Response(
                {'error': 'O\'quvchida faol abonement topilmadi'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Har bir abonement uchun to'lov xulosasini hisoblash
        results = []
        today = date.today()
        
        for subscription in subscriptions:
            payment_due = subscription.calculate_payment_due()
            
            results.append({
                'student_profile_id': str(student_profile.id),
                'student_name': student_profile.full_name,
                'subscription_id': str(subscription.id),
                'subscription_plan_name': subscription.subscription_plan.name,
                'subscription_period': subscription.subscription_plan.get_period_display(),
                'subscription_price': subscription.subscription_plan.price,
                'current_amount': payment_due['current_amount'],
                'debt_amount': payment_due['debt_amount'],
                'total_amount': payment_due['total_amount'],
                'next_due_date': payment_due['next_due_date'],
                'last_payment_date': subscription.last_payment_date,
                'overdue_months': payment_due['overdue_months'],
                'is_expired': payment_due['is_expired'],
                'is_overdue': today > subscription.next_payment_date if subscription.next_payment_date else False,
            })
        
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)
