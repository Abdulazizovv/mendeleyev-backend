import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import transaction
from django.db import models

from .serializers import (
    StudentCreateSerializer,
    StudentProfileSerializer,
    StudentRelativeCreateSerializer,
    StudentRelativeSerializer,
    UserCheckSerializer,
)
from auth.users.models import User
from .permissions import CanCreateStudent
from .filters import StudentProfileFilter
from auth.profiles.models import StudentProfile, StudentRelative
from apps.branch.models import BranchMembership, BranchRole


class StudentCreateView(APIView):
    """O'quvchi yaratish endpointi.
    
    Branch admin, super admin yoki sinf rahbar o'quvchi yaratishi mumkin.
    Telefon raqam tasdiqlash shart emas.
    """
    permission_classes = [IsAuthenticated, CanCreateStudent]
    
    @extend_schema(
        request=StudentCreateSerializer,
        responses={201: StudentProfileSerializer},
        summary="O'quvchi yaratish",
        description="""
        O'quvchi yaratish. Quyidagi rollarga ega foydalanuvchilar yaratishi mumkin:
        - super_admin
        - branch_admin (faqat o'z filialida)
        - teacher (faqat o'z sinfida sinf rahbar bo'lsa)
        
        **Xususiyatlar:**
        - Telefon raqam tasdiqlash shart emas
        - Barcha maydonlar ixtiyoriy (faqat phone_number va first_name majburiy)
        - Yaqinlarni bir vaqtning o'zida yaratish mumkin (nested serializer)
        - Barcha operatsiyalar atomic (bir xatoda bajariladi)
        - Sinfga biriktirish imkoniyati
        
        **Misol so'rov:**
        ```json
        {
          "phone_number": "+998901234567",
          "first_name": "Ali",
          "last_name": "Valiyev",
          "branch_id": "uuid",
          "middle_name": "Olim o'g'li",
          "gender": "male",
          "date_of_birth": "2010-05-15",
          "address": "Toshkent shahri",
          "class_id": "uuid",
          "relatives": [
            {
              "relationship_type": "father",
              "first_name": "Olim",
              "last_name": "Valiyev",
              "phone_number": "+998901234568",
              "is_primary_contact": true
            }
          ]
        }
        ```
        """
    )
    @transaction.atomic
    def post(self, request):
        serializer = StudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        student_profile = serializer.save()
        
        # StudentProfile serializer bilan qaytarish
        response_serializer = StudentProfileSerializer(student_profile)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class StudentListView(generics.ListAPIView):
    """O'quvchilar ro'yxati (paginatsiya, qidiruv, filter va ordering bilan)."""
    permission_classes = [IsAuthenticated]
    serializer_class = StudentProfileSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = StudentProfileFilter
    search_fields = [
        'personal_number',
        'user_branch__user__first_name',
        'user_branch__user__last_name',
        'middle_name',
        'user_branch__user__phone_number',
        'user_branch__user__email',
    ]
    ordering_fields = [
        'personal_number',
        'user_branch__user__first_name',
        'user_branch__user__last_name',
        'created_at',
        'date_of_birth',
        'gender',
        'status',
    ]
    ordering = ['-created_at']  # Default ordering
    
    @extend_schema(
        responses={200: StudentProfileSerializer(many=True)},
        summary="O'quvchilar ro'yxati",
        description="""
        Filial bo'yicha o'quvchilar ro'yxati (paginatsiya, qidiruv, filter va ordering bilan).
        
        Query parameters:
        - page: Sahifa raqami (default: 1)
        - page_size: Sahifadagi elementlar soni (default: 20, max: 100)
        - search: Qidirish (shaxsiy raqam, ism, telefon, email)
        - ordering: Tartiblash (masalan: created_at, -created_at, first_name, -first_name)
        - personal_number: Shaxsiy raqam bo'yicha qidirish
        - gender: Jinsi bo'yicha filter (male, female, other, unspecified)
        - date_of_birth: Tu'gilgan sana bo'yicha filter
        - date_of_birth__gte: Tu'gilgan sana (dan)
        - date_of_birth__lte: Tu'gilgan sana (gacha)
        - first_name: Ism bo'yicha qidirish
        - last_name: Familiya bo'yicha qidirish
        - phone_number: Telefon raqam bo'yicha qidirish
        - email: Email bo'yicha qidirish
        - branch_id: Filial ID bo'yicha filter
        - class_id: Sinf ID bo'yicha filter
        - grade_level: Sinf darajasi bo'yicha filter
        - created_at__gte: Yaratilgan sana (dan)
        - created_at__lte: Yaratilgan sana (gacha)
        """,
        parameters=[
            OpenApiParameter('search', OpenApiTypes.STR, description='Qidirish (shaxsiy raqam, ism, telefon, email)'),
            OpenApiParameter('ordering', OpenApiTypes.STR, description='Tartiblash (masalan: created_at, -created_at)'),
            OpenApiParameter('personal_number', OpenApiTypes.STR, description='Shaxsiy raqam bo\'yicha qidirish'),
            OpenApiParameter('gender', OpenApiTypes.STR, description='Jinsi bo\'yicha filter'),
            OpenApiParameter('date_of_birth', OpenApiTypes.DATE, description='Tu\'gilgan sana bo\'yicha filter'),
            OpenApiParameter('class_id', OpenApiTypes.UUID, description='Sinf ID bo\'yicha filter'),
            OpenApiParameter('grade_level', OpenApiTypes.INT, description='Sinf darajasi bo\'yicha filter'),
        ],
    )
    def get_queryset(self):
        # Branch ID ni olish
        branch_id = self._get_branch_id()
        if not branch_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "Filial ID talab qilinadi."})
        
        # Permissions tekshirish
        user = self.request.user
        if not user.is_superuser:
            has_role = BranchMembership.has_role(
                user.id,
                branch_id,
                [BranchRole.BRANCH_ADMIN, BranchRole.TEACHER]
            )
            if not has_role:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Ruxsat yo'q.")
        
        # O'quvchilarni olish
        from auth.profiles.models import StudentProfile
        
        queryset = StudentProfile.objects.filter(
            user_branch__branch_id=branch_id,
            user_branch__role=BranchRole.STUDENT,
            deleted_at__isnull=True,
            user_branch__deleted_at__isnull=True
        ).select_related(
            'user_branch',
            'user_branch__user',
            'user_branch__branch',
            'balance'  # StudentBalance - list view uchun faqat balans kerak
        ).prefetch_related('relatives')
        
        return queryset
    
    def _get_branch_id(self):
        """Branch ID ni olish."""
        from uuid import UUID
        
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
        
        # Query param (DRF Request obyekti uchun)
        if hasattr(self.request, 'query_params'):
            branch_id = self.request.query_params.get("branch_id")
        else:
            # WSGIRequest uchun
            branch_id = self.request.GET.get("branch_id")
        
        if branch_id:
            try:
                return str(UUID(str(branch_id)))
            except:
                pass
        
        return None


class StudentDetailView(APIView):
    """O'quvchi ma'lumotlari."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: StudentProfileSerializer},
        summary="O'quvchi ma'lumotlari",
        description="O'quvchi to'liq ma'lumotlari"
    )
    def get(self, request, student_id):
        try:
            student_profile = StudentProfile.objects.select_related(
                'user_branch',
                'user_branch__user',
                'user_branch__branch',
                'balance'  # StudentBalance
            ).prefetch_related(
                'relatives'
            ).get(
                id=student_id,
                deleted_at__isnull=True
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {"detail": "O'quvchi topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentProfileSerializer(
            student_profile,
            context={'include_finance_details': True}  # Detail view uchun barcha moliyaviy ma'lumotlar
        )
        return Response(serializer.data)


class StudentRelativeListView(APIView):
    """O'quvchi yaqinlari ro'yxati."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: StudentRelativeSerializer(many=True)},
        summary="O'quvchi yaqinlari",
        description="O'quvchi yaqinlari ro'yxati"
    )
    def get(self, request, student_id):
        try:
            student_profile = StudentProfile.objects.get(
                id=student_id,
                deleted_at__isnull=True
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {"detail": "O'quvchi topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        relatives = student_profile.relatives.filter(deleted_at__isnull=True)
        serializer = StudentRelativeSerializer(relatives, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=StudentRelativeCreateSerializer,
        responses={201: StudentRelativeSerializer},
        summary="O'quvchi yaqini qo'shish",
        description="O'quvchiga yaqin qo'shish"
    )
    def post(self, request, student_id):
        try:
            student_profile = StudentProfile.objects.get(
                id=student_id,
                deleted_at__isnull=True
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {"detail": "O'quvchi topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentRelativeCreateSerializer(data={
            **request.data,
            'student_profile': student_id
        })
        serializer.is_valid(raise_exception=True)
        relative = serializer.save()
        
        response_serializer = StudentRelativeSerializer(relative)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


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


class UserCheckView(PhoneLookupMixin, APIView):
    """Telefon raqam orqali user mavjudligini tekshirish.
    
    Avval berilgan filialda qidiradi, agar topilmasa barcha filiallarda qidiradi.
    """

    @extend_schema(
        summary="User mavjudligini tekshirish",
        description="""
        Telefon raqam orqali user mavjudligini tekshirish.
        
        Query/body parameters:
        - phone_number (required): Telefon raqami
        - branch_id (optional): Filial ID (agar berilmasa, barcha filiallarda qidiriladi)
        """,
        parameters=[
            OpenApiParameter('phone_number', OpenApiTypes.STR, description='Telefon raqami', required=False),
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID (ixtiyoriy)'),
        ],
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
        
        memberships = BranchMembership.objects.filter(
            user=user,
            deleted_at__isnull=True
        ).select_related(
            'branch',
            'user'
        ).prefetch_related('student_profile')
        
        all_branches_data = []
        branch_data = None
        
        for membership in memberships:
            data = {
                'branch_id': str(membership.branch.id),
                'branch_name': membership.branch.name,
                'role': membership.role,
                'role_display': membership.get_role_display(),
                'is_active': membership.is_active,
                'created_at': membership.created_at.isoformat() if membership.created_at else None,
                'user': {
                    'id': str(membership.user.id),
                    'phone_number': membership.user.phone_number,
                    'first_name': membership.user.first_name,
                    'last_name': membership.user.last_name,
                }
            }
            
            if membership.role == BranchRole.STUDENT and hasattr(membership, 'student_profile'):
                profile = membership.student_profile
                data['student_profile'] = {
                    'id': str(profile.id),
                    'personal_number': profile.personal_number,
                    'full_name': profile.full_name,
                    'status': profile.status,
                    'status_display': profile.get_status_display(),
                    'gender': profile.gender,
                    'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
                }
            else:
                data['student_profile'] = None
            
            all_branches_data.append(data)
            
            if branch_id and data['branch_id'] == branch_id:
                branch_data = data
        
        return Response({
            "exists_in_branch": branch_data is not None,
            "exists_globally": bool(all_branches_data),
            "branch_data": branch_data,
            "all_branches_data": all_branches_data,
        })


class StudentRelativeCheckView(PhoneLookupMixin, APIView):
    """Telefon raqam orqali o'quvchi yaqinlarini tekshirish."""

    @extend_schema(
        summary="O'quvchi yaqinlari mavjudligini tekshirish",
        description="""
        Telefon raqam orqali o'quvchi yaqinlari mavjudligini tekshirish.
        
        Query/body parameters:
        - phone_number (required): Telefon raqami
        - branch_id (optional): Filial ID (agar berilmasa, barcha filiallarda qidiriladi)
        """,
        parameters=[
            OpenApiParameter('phone_number', OpenApiTypes.STR, description='Telefon raqami', required=False),
            OpenApiParameter('branch_id', OpenApiTypes.UUID, description='Filial ID (ixtiyoriy)'),
        ],
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
        
        relatives = StudentRelative.objects.filter(
            self._build_phone_query(phone_variants),
            deleted_at__isnull=True
        ).select_related(
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
            'student_profile__user_branch__branch'
        )
        
        if not relatives.exists():
            return Response({
                "exists_in_branch": False,
                "exists_globally": False,
                "branch_data": None,
                "all_branches_data": [],
            })
        
        all_branches_data = []
        branch_data = None
        
        for relative in relatives:
            student_profile = relative.student_profile
            student_branch = student_profile.user_branch.branch
            
            data = {
                'id': str(relative.id),
                'relationship_type': relative.relationship_type,
                'relationship_type_display': relative.get_relationship_type_display(),
                'full_name': relative.full_name,
                'phone_number': relative.phone_number,
                'email': relative.email,
                'is_primary_contact': relative.is_primary_contact,
                'is_guardian': relative.is_guardian,
                'student': {
                    'id': str(student_profile.id),
                    'personal_number': student_profile.personal_number,
                    'full_name': student_profile.full_name,
                    'branch_id': str(student_branch.id),
                    'branch_name': student_branch.name,
                },
                'created_at': relative.created_at.isoformat() if relative.created_at else None,
            }
            
            all_branches_data.append(data)
            
            if branch_id and data['student']['branch_id'] == branch_id:
                branch_data = data
        
        return Response({
            "exists_in_branch": branch_data is not None,
            "exists_globally": True,
            "branch_data": branch_data,
            "all_branches_data": all_branches_data,
        })

