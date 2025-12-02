from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404

from apps.branch.models import Branch, BranchMembership
from apps.school.academic.models import AcademicYear
from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import Class, ClassStudent
from .serializers import (
    ClassSerializer,
    ClassCreateSerializer,
    ClassStudentSerializer,
    ClassStudentCreateSerializer,
)
from .filters import ClassFilter, ClassStudentFilter


class ClassListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Sinflar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ClassFilter
    search_fields = ['name', 'class_teacher__user__first_name', 'class_teacher__user__last_name']
    ordering_fields = ['name', 'grade_level', 'created_at', 'academic_year__start_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filial va akademik yil bo'yicha sinflarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Class.objects.filter(branch=branch, deleted_at__isnull=True).select_related(
            'branch',
            'academic_year',
            'class_teacher',
            'class_teacher__user',
            'room'
        ).prefetch_related('class_students__membership__user')
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClassCreateSerializer
        return ClassSerializer
    
    def perform_create(self, serializer):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        serializer.save(branch=branch, created_by=self.request.user)
    
    @extend_schema(
        summary="Sinflar ro'yxati",
        description="""
        Sinflar ro'yxati (paginatsiya, qidiruv, filter va ordering bilan).
        
        Query parameters:
        - page: Sahifa raqami (default: 1)
        - page_size: Sahifadagi elementlar soni (default: 20, max: 100)
        - search: Qidirish (nomi, sinf rahbari)
        - ordering: Tartiblash (masalan: name, -name, grade_level, -grade_level)
        - academic_year_id: Akademik yil ID bo'yicha filter
        - grade_level: Sinf darajasi bo'yicha filter
        - section: Bo'lim bo'yicha filter
        - is_active: Faol sinflar bo'yicha filter
        - class_teacher_id: Sinf rahbari ID bo'yicha filter
        - room_id: Xona ID bo'yicha filter
        """,
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('academic_year_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('grade_level', type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi sinf yaratish",
        request=ClassCreateSerializer,
        responses={201: ClassSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ClassDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Sinf detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = ClassSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return Class.objects.filter(branch=branch, deleted_at__isnull=True).select_related(
            'branch',
            'academic_year',
            'class_teacher',
            'class_teacher__user'
        ).prefetch_related('class_students__membership__user')
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Sinf detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinfni yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinfni o'chirish",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ClassStudentListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Sinf o'quvchilari ro'yxati va qo'shish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = ClassStudentSerializer
    filterset_class = ClassStudentFilter
    search_fields = [
        'membership__user__first_name',
        'membership__user__last_name',
        'membership__user__phone_number',
    ]
    ordering_fields = ['created_at', 'membership__user__first_name', 'membership__user__last_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Sinf o'quvchilarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id, deleted_at__isnull=True)
        
        queryset = ClassStudent.objects.filter(
            class_obj=class_obj,
            deleted_at__isnull=True
        ).select_related(
            'membership',
            'membership__user',
            'class_obj'
        )
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClassStudentCreateSerializer
        return ClassStudentSerializer
    
    def get_serializer_context(self):
        """Add class_obj to serializer context."""
        context = super().get_serializer_context()
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        context['class_obj'] = class_obj
        return context
    
    def perform_create(self, serializer):
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        serializer.save(class_obj=class_obj, created_by=self.request.user)
    
    @extend_schema(
        summary="Sinf o'quvchilari ro'yxati",
        description="""
        Sinf o'quvchilari ro'yxati (paginatsiya, qidiruv, filter va ordering bilan).
        
        Query parameters:
        - page: Sahifa raqami (default: 1)
        - page_size: Sahifadagi elementlar soni (default: 20, max: 100)
        - search: Qidirish (ism, telefon)
        - ordering: Tartiblash (masalan: created_at, -created_at)
        - is_active: Faol o'quvchilar bo'yicha filter
        """,
        parameters=[
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('search', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('ordering', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchi qo'shish",
        request=ClassStudentCreateSerializer,
        responses={201: ClassStudentSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ClassStudentDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Sinf o'quvchisi detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = ClassStudentSerializer
    lookup_url_kwarg = 'student_id'
    
    def get_queryset(self):
        """Sinf o'quvchilarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id, deleted_at__isnull=True)
        return ClassStudent.objects.filter(class_obj=class_obj, deleted_at__isnull=True).select_related(
            'membership',
            'membership__user',
            'class_obj'
        )
    
    def get_object(self):
        """O'quvchini membership_id orqali topadi."""
        queryset = self.get_queryset()
        student_id = self.kwargs.get('student_id')
        obj = get_object_or_404(queryset, membership_id=student_id)
        return obj
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="O'quvchi detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchini yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="O'quvchini olib tashlash",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

