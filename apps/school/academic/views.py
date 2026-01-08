from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.branch.models import Branch
from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import AcademicYear, Quarter
from .serializers import (
    AcademicYearSerializer,
    AcademicYearCreateSerializer,
    QuarterSerializer,
    QuarterCreateSerializer,
)


class AcademicYearListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Akademik yillar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'name']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """Filial bo'yicha akademik yillarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return AcademicYear.objects.filter(branch=branch, deleted_at__isnull=True).prefetch_related('quarters')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AcademicYearCreateSerializer
        return AcademicYearSerializer

    def get_permissions(self):
        """Apply action-based branch roles: read is broad, write is restricted."""
        # Broad read for branch members (including teacher, student, parent, other)
        read_roles = ("branch_admin", "super_admin", "teacher", "student", "parent", "other")
        write_roles = ("branch_admin", "super_admin")
        self.required_branch_roles = read_roles if self.request.method in SAFE_METHODS else write_roles
        return super().get_permissions()
    
    def perform_create(self, serializer):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        serializer.save(branch=branch, created_by=self.request.user)
    
    @extend_schema(
        summary="Akademik yillar ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi akademik yil yaratish",
        request=AcademicYearCreateSerializer,
        responses={201: AcademicYearSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AcademicYearDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Akademik yil detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin")
    serializer_class = AcademicYearSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return AcademicYear.objects.filter(branch=branch).prefetch_related('quarters')
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def get_permissions(self):
        """Apply action-based branch roles: read is broad, write is restricted."""
        read_roles = ("branch_admin", "super_admin", "teacher", "student", "parent", "other")
        write_roles = ("branch_admin", "super_admin")
        self.required_branch_roles = read_roles if self.request.method in SAFE_METHODS else write_roles
        return super().get_permissions()
    
    @extend_schema(
        summary="Akademik yil detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Akademik yilni yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Akademik yilni o'chirish",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class QuarterListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Choraklar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'number']
    ordering = ['number']
    
    def get_queryset(self):
        """Akademik yil bo'yicha choraklarni qaytaradi."""
        academic_year_id = self.kwargs.get('academic_year_id')
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        return Quarter.objects.filter(academic_year=academic_year)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuarterCreateSerializer
        return QuarterSerializer

    def get_permissions(self):
        """Apply action-based branch roles: read is broad, write is restricted."""
        read_roles = ("branch_admin", "super_admin", "teacher", "student", "parent", "other")
        write_roles = ("branch_admin", "super_admin")
        self.required_branch_roles = read_roles if self.request.method in SAFE_METHODS else write_roles
        return super().get_permissions()
    
    def perform_create(self, serializer):
        academic_year_id = self.kwargs.get('academic_year_id')
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        serializer.save(academic_year=academic_year, created_by=self.request.user)
    
    @extend_schema(
        summary="Choraklar ro'yxati",
        parameters=[
            OpenApiParameter('academic_year_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi chorak yaratish",
        request=QuarterCreateSerializer,
        responses={201: QuarterSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CurrentAcademicYearView(generics.RetrieveAPIView):
    """Joriy akademik yil va chorak."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher", "student", "parent")
    serializer_class = AcademicYearSerializer
    
    def get_object(self):
        """Joriy akademik yilni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        academic_year = AcademicYear.objects.filter(
            branch=branch,
            is_active=True,
            delete_at__isnull=True
        ).prefetch_related('quarters').first()
        
        if not academic_year:
            from rest_framework.exceptions import NotFound
            raise NotFound('Joriy akademik yil topilmadi.')
        
        return academic_year
    
    @extend_schema(
        summary="Joriy akademik yil va chorak",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class CurrentQuarterView(generics.RetrieveAPIView):
    """Joriy aktiv chorak."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher", "student", "parent")
    serializer_class = QuarterSerializer
    
    def get_object(self):
        """
        Joriy aktiv chorakni qaytaradi.
        Agar hech qanday aktiv chorak yo'q bo'lsa, bugungi sanaga mos chorakni qaytaradi.
        """
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        # Avval aktiv akademik yilni topamiz
        academic_year = AcademicYear.objects.filter(
            branch=branch,
            is_active=True
        ).first()
        
        if not academic_year:
            from rest_framework.exceptions import NotFound
            raise NotFound('Joriy akademik yil topilmadi.')
        
        # Avval is_active=True chorakni qidiramiz
        quarter = Quarter.objects.filter(
            academic_year=academic_year,
            is_active=True
        ).first()
        
        if quarter:
            return quarter
        
        # Agar yo'q bo'lsa, bugungi sanaga mos chorakni topamiz
        today = timezone.now().date()
        quarter = Quarter.objects.filter(
            academic_year=academic_year,
            start_date__lte=today,
            end_date__gte=today
        ).first()
        
        if not quarter:
            raise NotFound('Joriy chorak topilmadi. Iltimos, choraklarni tekshiring.')
        
        return quarter
    
    @extend_schema(
        summary="Joriy aktiv chorak",
        description="Joriy aktiv chorakni qaytaradi. Agar is_active=True chorak yo'q bo'lsa, bugungi sanaga mos chorakni qaytaradi.",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
