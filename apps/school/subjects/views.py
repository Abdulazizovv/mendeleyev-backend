from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404

from apps.branch.models import Branch
from apps.school.classes.models import Class
from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import Subject, ClassSubject
from .serializers import (
    SubjectSerializer,
    SubjectCreateSerializer,
    ClassSubjectSerializer,
    ClassSubjectCreateSerializer,
)
from .filters import SubjectFilter, ClassSubjectFilter


class SubjectListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Fanlar ro'yxati va yaratish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SubjectFilter
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filial bo'yicha fanlarni qaytaradi."""
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        
        queryset = Subject.objects.filter(branch=branch)
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SubjectCreateSerializer
        return SubjectSerializer
    
    def perform_create(self, serializer):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        serializer.save(branch=branch, created_by=self.request.user)
    
    @extend_schema(
        summary="Fanlar ro'yxati",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Yangi fan yaratish",
        request=SubjectCreateSerializer,
        responses={201: SubjectSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SubjectDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Fan detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = SubjectSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        branch = get_object_or_404(Branch, id=branch_id)
        return Subject.objects.filter(branch=branch)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Fan detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Fanni yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Fanni o'chirish",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class ClassSubjectListView(AuditTrailMixin, generics.ListCreateAPIView):
    """Sinf fanlari ro'yxati va qo'shish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = ClassSubjectSerializer
    filterset_class = ClassSubjectFilter
    search_fields = [
        'subject__name',
        'teacher__user__first_name',
        'teacher__user__last_name',
    ]
    ordering_fields = ['created_at', 'subject__name']
    ordering = ['subject__name']
    
    def get_queryset(self):
        """Sinf fanlarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        
        queryset = ClassSubject.objects.filter(
            class_obj=class_obj
        ).select_related(
            'class_obj',
            'subject',
            'teacher',
            'teacher__user',
            'quarter'
        )
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClassSubjectCreateSerializer
        return ClassSubjectSerializer
    
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
        summary="Sinf fanlari ro'yxati",
        parameters=[
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.PATH),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinfga fan qo'shish",
        request=ClassSubjectCreateSerializer,
        responses={201: ClassSubjectSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ClassSubjectDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Sinf fani detallari, yangilash va o'chirish."""
    
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ("branch_admin", "super_admin", "teacher")
    serializer_class = ClassSubjectSerializer
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        """Sinf fanlarini qaytaradi."""
        class_id = self.kwargs.get('class_id')
        class_obj = get_object_or_404(Class, id=class_id)
        return ClassSubject.objects.filter(class_obj=class_obj).select_related(
            'class_obj',
            'subject',
            'teacher',
            'teacher__user',
            'quarter'
        )
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @extend_schema(
        summary="Sinf fani detallari",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinf fani yangilash",
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Sinfdan fanni olib tashlash",
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

