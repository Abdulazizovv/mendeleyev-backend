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
from .permissions import CanManageFinance, CanViewFinanceReports, CanManageCategories
from .filters import (
    TransactionFilter,
    PaymentFilter,
    StudentSubscriptionFilter,
    FinanceCategoryFilter,
    DiscountFilter,
    SubscriptionPlanFilter,
    CashRegisterFilter,
)
from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile


class BaseFinanceView:
    """Asosiy moliya view mixin."""
    
    def _get_branch_id(self, allow_body=False):
        """
        Branch ID ni olish.
        
        MUHIM: Agar user bir nechta filialga a'zo bo'lsa, frontend MAJBURIY
        ravishda branch_id yuborishi kerak (header, query param yoki body orqali).
        
        Prioritet tartibi:
        1. Query parameter: ?branch_id=... (GET uchun)
        2. HTTP Header: X-Branch-Id
        3. Request body: {"branch_id": "..."} (POST/PUT uchun, agar allow_body=True)
        4. JWT token: br yoki branch_id claim
        5. Middleware: request.branch_id
        6. Fallback: Bitta membership bo'lsa avtomatik
        
        Returns:
            str: Branch UUID yoki None
        """
        import logging
        logger = logging.getLogger(__name__)
        
        user_id = self.request.user.id if self.request.user else None
        
        # Debug: Request ma'lumotlarini log qilish
        logger.info(f"""
╔══════════════════════════════════════════════════════════╗
║ 🔍 _get_branch_id() DEBUG                                 ║
╠══════════════════════════════════════════════════════════╣
║ User ID: {user_id}
║ Method: {self.request.method}
║ Path: {self.request.path}
║ Headers (X-Branch-Id): {self.request.META.get('HTTP_X_BRANCH_ID')}
║ Query params: {dict(self.request.query_params) if hasattr(self.request, 'query_params') else dict(self.request.GET)}
║ JWT auth type: {type(self.request.auth)}
║ JWT auth value: {self.request.auth if isinstance(self.request.auth, dict) else 'Not a dict'}
║ Allow body: {allow_body}
╚══════════════════════════════════════════════════════════╝
        """)
        
        # 1. Query parameter (eng yuqori prioritet GET uchun)
        if self.request.method == 'GET':
            qp_branch_id = None
            if hasattr(self.request, 'query_params'):
                qp_branch_id = self.request.query_params.get("branch_id")
            else:
                qp_branch_id = self.request.GET.get("branch_id")
            
            if qp_branch_id:
                try:
                    branch_id_uuid = str(UUID(str(qp_branch_id)))
                    # Access tekshirish
                    has_access = BranchMembership.objects.filter(
                        user=self.request.user,
                        branch_id=branch_id_uuid,
                        deleted_at__isnull=True
                    ).exists()
                    if has_access:
                        logger.info(f"✅ Branch ID from QUERY PARAM: {branch_id_uuid}")
                        return branch_id_uuid
                    else:
                        logger.warning(f"⛔ Query param branch_id={branch_id_uuid} access denied")
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Invalid query param branch_id: {qp_branch_id}, error: {e}")
        
        # 2. HTTP Header
        header_branch_id = self.request.META.get("HTTP_X_BRANCH_ID")
        if header_branch_id:
            try:
                branch_id_uuid = str(UUID(str(header_branch_id)))
                # Access tekshirish
                has_access = BranchMembership.objects.filter(
                    user=self.request.user,
                    branch_id=branch_id_uuid,
                    deleted_at__isnull=True
                ).exists()
                if has_access:
                    logger.info(f"✅ Branch ID from HEADER: {branch_id_uuid}")
                    return branch_id_uuid
                else:
                    logger.warning(f"⛔ Header branch_id={branch_id_uuid} access denied")
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ Invalid header branch_id: {header_branch_id}, error: {e}")
        
        # 3. Request body (POST/PUT uchun, agar allow_body=True)
        if allow_body and hasattr(self.request, 'data'):
            body_branch_id = self.request.data.get('branch_id')
            if body_branch_id:
                try:
                    branch_id_uuid = str(UUID(str(body_branch_id)))
                    # Access tekshirish
                    has_access = BranchMembership.objects.filter(
                        user=self.request.user,
                        branch_id=branch_id_uuid,
                        deleted_at__isnull=True
                    ).exists()
                    if has_access:
                        logger.info(f"✅ Branch ID from BODY: {branch_id_uuid}")
                        return branch_id_uuid
                    else:
                        logger.warning(f"⛔ Body branch_id={branch_id_uuid} access denied")
                except (ValueError, TypeError) as e:
                    logger.warning(f"⚠️ Invalid body branch_id: {body_branch_id}, error: {e}")
        
        # 4. JWT token claim
        if hasattr(self.request, "auth") and self.request.auth:
            logger.info(f"JWT auth type: {type(self.request.auth)}, value: {self.request.auth}")
            
            # SimpleJWT AccessToken object
            if hasattr(self.request.auth, 'payload'):
                payload = self.request.auth.payload
                logger.info(f"JWT payload: {payload}")
                br_claim = payload.get("br") or payload.get("branch_id")
                if br_claim:
                    try:
                        branch_id_uuid = str(UUID(str(br_claim)))
                        logger.info(f"✅ Branch ID from JWT (SimpleJWT): {branch_id_uuid}")
                        return branch_id_uuid
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Invalid JWT branch_id: {br_claim}, error: {e}")
            
            # Dict (legacy support)
            elif isinstance(self.request.auth, dict):
                br_claim = self.request.auth.get("br") or self.request.auth.get("branch_id")
                if br_claim:
                    try:
                        branch_id_uuid = str(UUID(str(br_claim)))
                        logger.info(f"✅ Branch ID from JWT (dict): {branch_id_uuid}")
                        return branch_id_uuid
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Invalid JWT branch_id: {br_claim}, error: {e}")
        
        # 5. Middleware
        if hasattr(self.request, 'branch_id') and self.request.branch_id:
            logger.info(f"✅ Branch ID from MIDDLEWARE: {self.request.branch_id}")
            return self.request.branch_id
        
        # 6. FALLBACK: Bitta membership bo'lsa
        logger.info("🔄 Fallback: Checking user memberships...")
        memberships = BranchMembership.objects.filter(
            user=self.request.user,
            deleted_at__isnull=True
        ).select_related('branch')
        
        membership_count = memberships.count()
        logger.info(f"📊 User has {membership_count} membership(s)")
        
        if membership_count == 1:
            membership = memberships.first()
            branch_id = str(membership.branch_id)
            logger.info(f"✅ Branch ID from SINGLE MEMBERSHIP: {branch_id} (branch: {membership.branch.name})")
            return branch_id
        elif membership_count > 1:
            logger.warning(f"⚠️ User has {membership_count} memberships - explicit branch_id REQUIRED!")
            for m in memberships:
                logger.info(f"   - {m.branch.name} ({m.branch_id}) - {m.role}")
            return None
        else:
            logger.error(f"❌ User has NO memberships!")
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
    
    def _get_user_membership(self, branch_id=None):
        """User ning BranchMembership ni olish.
        
        Args:
            branch_id: Aniq branch uchun membership. Agar berilmasa, _get_branch_id() dan olinadi.
        
        Returns:
            BranchMembership yoki None
        """
        try:
            # Agar branch_id berilmagan bo'lsa, _get_branch_id() dan olish
            if branch_id is None:
                branch_id = self._get_branch_id()
            
            # Agar branch_id topilmasa, birinchi membership
            if not branch_id:
                return BranchMembership.objects.filter(
                    user=self.request.user,
                    deleted_at__isnull=True
                ).first()
            
            # Aniq branch uchun membership
            return BranchMembership.objects.filter(
                user=self.request.user,
                branch_id=branch_id,
                deleted_at__isnull=True
            ).first()
        except Exception:
            return None
    
    def _should_auto_approve(self):
        """Tranzaksiya avtomatik tasdiqlanishi kerakmi?
        
        Logika:
        - Branch Admin: har doim auto-approve
        - Super Admin: permission-based (CAN_AUTO_APPROVE)
        - Accountant/boshqa rollar: permission-based (CAN_AUTO_APPROVE)
        """
        from .permissions import FinancePermissions
        
        # Super admin tekshiruvi
        if self._is_super_admin():
            # Super admin uchun permission-based
            membership = self._get_user_membership()
            if membership and membership.role_ref:
                permissions = membership.role_ref.permissions or {}
                return permissions.get(FinancePermissions.CAN_AUTO_APPROVE, False)
            return False
        
        # Branch admin - har doim avtomatik tasdiqlanadi
        try:
            membership = BranchMembership.objects.filter(
                user=self.request.user,
                deleted_at__isnull=True
            ).first()
            if membership and membership.role == BranchRole.BRANCH_ADMIN:
                return True
            
            # Boshqa rollar uchun permission-based
            if membership and membership.role_ref:
                permissions = membership.role_ref.permissions or {}
                return permissions.get(FinancePermissions.CAN_AUTO_APPROVE, False)
        except Exception:
            pass
        
        # Default: manual tasdiq
        return False


# ==================== Finance Category Views ====================

@extend_schema(tags=['Finance Categories'])
class FinanceCategoryListCreateView(BaseFinanceView, generics.ListCreateAPIView):
    """Kategoriyalar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = FinanceCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FinanceCategoryFilter
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
    filterset_class = CashRegisterFilter
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
        import logging
        logger = logging.getLogger(__name__)
        
        queryset = CashRegister.objects.filter(
            deleted_at__isnull=True
        ).select_related('branch')
        
        # Super admin barcha kassalarni ko'radi
        if not self._is_super_admin():
            branch_id = self._get_branch_id()
            logger.warning(f"🔍 CashRegisterDetailView: user={self.request.user.id}, branch_id={branch_id}, query_params={dict(self.request.query_params) if hasattr(self.request, 'query_params') else {}}")
            if not branch_id:
                return CashRegister.objects.none()
            queryset = queryset.filter(branch_id=branch_id)
        
        return queryset


# ==================== Transaction Views ====================

class TransactionListView(generics.ListCreateAPIView, BaseFinanceView):
    """Tranzaksiyalar ro'yxati va yaratish."""
    permission_classes = [IsAuthenticated, CanManageFinance]
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['description', 'reference_number', 'student_profile__personal_number']
    ordering_fields = ['amount', 'transaction_date', 'created_at', 'status']
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
        ).prefetch_related(
            'payment',  # Transaction->Payment reverse relation (OneToOne)
        )
        
        # Super admin barcha tranzaksiyalarni ko'radi
        if not self._is_super_admin():
            branch_id = self._get_branch_id()
            if not branch_id:
                return Transaction.objects.none()
            queryset = queryset.filter(branch_id=branch_id)
        
        # Soft delete filtri
        queryset = queryset.filter(deleted_at__isnull=True)
        
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
    filterset_class = SubscriptionPlanFilter
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
    filterset_class = DiscountFilter
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
    filterset_class = PaymentFilter
    search_fields = ['student_profile__personal_number', 'notes', 'student_profile__user_branch__user__first_name']
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
    filterset_class = StudentSubscriptionFilter
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


# ==================== Export Views ====================

class ExportTransactionsView(BaseFinanceView, generics.GenericAPIView):
    """Tranzaksiyalarni Excel ga export qilish."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    
    @extend_schema(
        summary="Tranzaksiyalarni Excel ga export qilish",
        description="Tranzaksiyalarni Excel fayliga export qilish. Celery task orqali asinxron bajariladi.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('transaction_type', OpenApiTypes.STR, description='Tranzaksiya turi'),
            OpenApiParameter('status', OpenApiTypes.STR, description='Holat'),
            OpenApiParameter('date_from', OpenApiTypes.DATE, description='Boshlanish sanasi'),
            OpenApiParameter('date_to', OpenApiTypes.DATE, description='Tugash sanasi'),
            OpenApiParameter('cash_register', OpenApiTypes.UUID, description='Kassa ID'),
            OpenApiParameter('category', OpenApiTypes.UUID, description='Kategoriya ID'),
            OpenApiParameter('student_profile', OpenApiTypes.UUID, description='O\'quvchi ID'),
        ],
    )
    def post(self, request):
        """Export taskni boshlash."""
        from .tasks import export_transactions_to_excel
        import logging
        logger = logging.getLogger(__name__)
        
        # User membership va role tekshirish
        user_membership = self._get_user_membership()
        if not user_membership:
            return Response(
                {'error': 'Siz hech qaysi filialga tegishli emassiz'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logger.info(f"Export request from user: {request.user.id}, role: {user_membership.role_ref.name if user_membership.role_ref else 'None'}, membership_branch: {user_membership.branch_id}")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request headers X-Branch-Id: {request.META.get('HTTP_X_BRANCH_ID')}")
        
        # Branch Admin: Faqat o'z branchidan export olsin
        is_branch_admin = user_membership.role_ref and user_membership.role_ref.name == BranchRole.BRANCH_ADMIN
        
        if is_branch_admin:
            # Branch Admin faqat o'z branchidan export olishi mumkin (JWT dan)
            branch_id = str(user_membership.branch_id)
            logger.info(f"Branch Admin detected. Using branch_id from membership: {branch_id}")
            
            # Agar header da boshqa branch_id berilgan bo'lsa, xatolik
            header_branch_id = self._get_branch_id()
            if header_branch_id and str(header_branch_id) != branch_id:
                logger.warning(f"Branch Admin tried to access different branch. Header: {header_branch_id}, Own: {branch_id}")
                return Response(
                    {'error': 'Siz faqat o\'z filialingizdan export olishingiz mumkin'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Super Admin va boshqalar: Header yoki body dan
            branch_id = self._get_branch_id(allow_body=True)  # ✅ Body dan ham olsin
            logger.info(f"Non-Branch Admin. Branch ID: {branch_id}")
            
            if not branch_id:
                return Response(
                    {'error': 'Branch ID talab qilinadi (X-Branch-Id header yoki branch_id body da)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        logger.info(f"Final branch_id for export: {branch_id}")
        
        # Filterlarni olish
        filters = {}
        if request.data.get('transaction_type'):
            filters['transaction_type'] = request.data.get('transaction_type')
        if request.data.get('status'):
            filters['status'] = request.data.get('status')
        if request.data.get('date_from'):
            filters['date_from'] = request.data.get('date_from')
        if request.data.get('date_to'):
            filters['date_to'] = request.data.get('date_to')
        if request.data.get('cash_register'):
            filters['cash_register'] = request.data.get('cash_register')
        if request.data.get('category'):
            filters['category'] = request.data.get('category')
        if request.data.get('student_profile'):
            filters['student_profile'] = request.data.get('student_profile')
        
        # Celery taskni boshlash
        task = export_transactions_to_excel.delay(
            branch_id=branch_id,
            filters=filters,
            user_id=str(request.user.id)
        )
        
        return Response({
            'message': 'Export task boshlandi',
            'task_id': task.id,
            'status': 'PENDING'
        }, status=status.HTTP_202_ACCEPTED)


class ExportPaymentsView(BaseFinanceView, generics.GenericAPIView):
    """To'lovlarni Excel ga export qilish."""
    
    permission_classes = [IsAuthenticated, CanManageFinance]
    
    @extend_schema(
        summary="To'lovlarni Excel ga export qilish",
        description="To'lovlarni Excel fayliga export qilish. Celery task orqali asinxron bajariladi.",
        parameters=[
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID'),
            OpenApiParameter('student_profile', OpenApiTypes.UUID, description='O\'quvchi ID'),
            OpenApiParameter('date_from', OpenApiTypes.DATE, description='Boshlanish sanasi'),
            OpenApiParameter('date_to', OpenApiTypes.DATE, description='Tugash sanasi'),
            OpenApiParameter('period', OpenApiTypes.STR, description='Davr'),
        ],
    )
    def post(self, request):
        """Export taskni boshlash."""
        from .tasks import export_payments_to_excel
        
        # User membership va role tekshirish
        user_membership = self._get_user_membership()
        if not user_membership:
            return Response(
                {'error': 'Siz hech qaysi filialga tegishli emassiz'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Branch Admin: Faqat o'z branchidan export olsin
        is_branch_admin = user_membership.role_ref and user_membership.role_ref.name == BranchRole.BRANCH_ADMIN
        
        if is_branch_admin:
            # Branch Admin faqat o'z branchidan export olishi mumkin
            branch_id = str(user_membership.branch_id)
            
            # Agar header/body da boshqa branch_id berilgan bo'lsa, xatolik
            requested_branch_id = self._get_branch_id() or request.data.get('branch_id')
            if requested_branch_id and str(requested_branch_id) != branch_id:
                return Response(
                    {'error': 'Siz faqat o\'z filialingizdan export olishingiz mumkin'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Super Admin va boshqalar: Istalgan branchdan (header/body dan)
            branch_id = self._get_branch_id()
            
            # Agar header da yo'q bo'lsa, body dan olamiz
            if not branch_id and request.data.get('branch_id'):
                branch_id = request.data.get('branch_id')
            
            if not branch_id:
                return Response(
                    {'error': 'Branch ID talab qilinadi (X-Branch-Id header yoki branch_id body da)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Filterlarni olish
        filters = {}
        if request.data.get('student_profile'):
            filters['student_profile'] = request.data.get('student_profile')
        if request.data.get('date_from'):
            filters['date_from'] = request.data.get('date_from')
        if request.data.get('date_to'):
            filters['date_to'] = request.data.get('date_to')
        if request.data.get('period'):
            filters['period'] = request.data.get('period')
        
        # Celery taskni boshlash
        task = export_payments_to_excel.delay(
            branch_id=branch_id,
            filters=filters,
            user_id=str(request.user.id)
        )
        
        return Response({
            'message': 'Export task boshlandi',
            'task_id': task.id,
            'status': 'PENDING'
        }, status=status.HTTP_202_ACCEPTED)


class ExportTaskStatusView(generics.GenericAPIView):
    """Export task statusini olish."""
    
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Export task statusini olish",
        description="Celery task natijasini olish. Task bajarilganda fayl URL ni qaytaradi.",
    )
    def get(self, request, task_id):
        """Task statusini va natijasini olish."""
        from celery.result import AsyncResult
        
        task = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': task.state,
        }
        
        if task.state == 'PENDING':
            response_data['message'] = 'Task kutilmoqda'
        elif task.state == 'STARTED':
            response_data['message'] = 'Task bajarilmoqda'
        elif task.state == 'SUCCESS':
            result = task.result
            if result and result.get('success'):
                response_data['message'] = 'Export muvaffaqiyatli'
                response_data['file_url'] = result.get('file_url')
                response_data['filename'] = result.get('filename')
                response_data['records_count'] = result.get('records_count')
            else:
                response_data['message'] = 'Export xatolik'
                response_data['error'] = result.get('error', 'Noma\'lum xatolik')
        elif task.state == 'FAILURE':
            response_data['message'] = 'Task xatolik'
            response_data['error'] = str(task.info)
        else:
            response_data['message'] = f'Task holati: {task.state}'
        
        return Response(response_data)
