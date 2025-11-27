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
)
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
        
        Telefon raqam tasdiqlash shart emas.
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
            'user_branch__branch'
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
                'user_branch__branch'
            ).prefetch_related('relatives').get(
                id=student_id,
                deleted_at__isnull=True
            )
        except StudentProfile.DoesNotExist:
            return Response(
                {"detail": "O'quvchi topilmadi."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = StudentProfileSerializer(student_profile)
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

