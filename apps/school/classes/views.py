from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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


class ClassListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Sinflar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    
    def get_queryset(self):
        """Filial va akademik yil bo'yicha sinflarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Class.objects.filter(branch=branch).select_related(
            'branch',
            'academic_year',
            'class_teacher',
            'class_teacher__user'
        ).prefetch_related('class_students__membership__user')
        
        # Filter by academic_year if provided
        academic_year_id = self.request.query_params.get('academic_year_id')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        # Filter by grade_level if provided
        grade_level = self.request.query_params.get('grade_level')
        if grade_level:
            queryset = queryset.filter(grade_level=grade_level)
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
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
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
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
        return Class.objects.filter(branch=branch).select_related(
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
    serializer_class = ClassStudentSerializer
    
    def get_queryset(self):
        """Sinf o'quvchilarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        
        queryset = ClassStudent.objects.filter(
            class_obj=class_obj
        ).select_related(
            'membership',
            'membership__user',
            'class_obj'
        )
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
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
        parameters=[
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
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
        class_obj = get_object_or_404(Class, id=class_id)
        return ClassStudent.objects.filter(class_obj=class_obj).select_related(
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

