from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.shortcuts import get_object_or_404
from django.db.models import Q

from apps.branch.models import BranchMembership
from apps.common.permissions import HasBranchRole, IsTeacher, IsStudent
from apps.school.classes.models import Class, ClassStudent
from apps.school.subjects.models import ClassSubject
from .serializers import (
    TeacherClassSerializer,
    TeacherSubjectSerializer,
    TeacherStudentSerializer,
    StudentClassSerializer,
    StudentSubjectSerializer,
)


class TeacherClassesView(generics.ListAPIView):
    """O'qituvchining sinflari."""
    
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherClassSerializer
    
    def get_queryset(self):
        """O'qituvchining sinflarini qaytaradi."""
        user = self.request.user
        
        # JWT dan branch_id olish
        branch_id = None
        if hasattr(self.request, 'auth') and isinstance(self.request.auth, dict):
            branch_id = self.request.auth.get('br')
        
        if not branch_id:
            # Header yoki query param dan olish
            branch_id = self.request.META.get('HTTP_X_BRANCH_ID') or self.request.query_params.get('branch_id')
        
        if not branch_id:
            return Class.objects.none()
        
        # O'qituvchi membership
        teacher_membership = get_object_or_404(
            BranchMembership,
            user=user,
            branch_id=branch_id,
            role='teacher',
            deleted_at__isnull=True
        )
        
        # O'qituvchi class_teacher yoki ClassSubject orqali biriktirilgan sinflar
        queryset = Class.objects.filter(
            Q(class_teacher=teacher_membership) |
            Q(class_subjects__teacher=teacher_membership)
        ).filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).distinct().select_related(
            'branch',
            'academic_year',
            'class_teacher',
            'class_teacher__user',
            'room'
        ).prefetch_related('class_subjects')
        
        # Filter by academic_year if provided
        academic_year_id = self.request.query_params.get('academic_year_id')
        if academic_year_id:
            queryset = queryset.filter(academic_year_id=academic_year_id)
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    @extend_schema(
        summary="O'qituvchining sinflari",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False, description='Filial ID (JWT dan yoki header dan olinadi)'),
            OpenApiParameter('academic_year_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TeacherSubjectsView(generics.ListAPIView):
    """O'qituvchining fanlari."""
    
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherSubjectSerializer
    
    def get_queryset(self):
        """O'qituvchining fanlarini qaytaradi."""
        user = self.request.user
        
        # JWT dan branch_id olish
        branch_id = None
        if hasattr(self.request, 'auth') and isinstance(self.request.auth, dict):
            branch_id = self.request.auth.get('br')
        
        if not branch_id:
            branch_id = self.request.META.get('HTTP_X_BRANCH_ID') or self.request.query_params.get('branch_id')
        
        if not branch_id:
            return ClassSubject.objects.none()
        
        # O'qituvchi membership
        teacher_membership = get_object_or_404(
            BranchMembership,
            user=user,
            branch_id=branch_id,
            role='teacher',
            deleted_at__isnull=True
        )
        
        # O'qituvchining fanlari
        queryset = ClassSubject.objects.filter(
            teacher=teacher_membership,
            deleted_at__isnull=True
        ).select_related(
            'class_obj',
            'class_obj__academic_year',
            'subject',
            'teacher',
            'teacher__user',
            'quarter'
        )
        
        # Filter by class_id if provided
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    @extend_schema(
        summary="O'qituvchining fanlari",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('is_active', type=OpenApiTypes.BOOL, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class TeacherStudentsView(generics.ListAPIView):
    """O'qituvchining o'quvchilari."""
    
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherStudentSerializer
    
    def get_queryset(self):
        """O'qituvchining o'quvchilarini qaytaradi."""
        user = self.request.user
        
        # JWT dan branch_id olish
        branch_id = None
        if hasattr(self.request, 'auth') and isinstance(self.request.auth, dict):
            branch_id = self.request.auth.get('br')
        
        if not branch_id:
            branch_id = self.request.META.get('HTTP_X_BRANCH_ID') or self.request.query_params.get('branch_id')
        
        if not branch_id:
            return ClassStudent.objects.none()
        
        # O'qituvchi membership
        teacher_membership = get_object_or_404(
            BranchMembership,
            user=user,
            branch_id=branch_id,
            role='teacher',
            deleted_at__isnull=True
        )
        
        # O'qituvchining sinflari
        teacher_classes = Class.objects.filter(
            Q(class_teacher=teacher_membership) |
            Q(class_subjects__teacher=teacher_membership)
        ).filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        ).distinct()
        
        # O'qituvchining sinflaridagi o'quvchilar
        queryset = ClassStudent.objects.filter(
            class_obj__in=teacher_classes,
            deleted_at__isnull=True,
            is_active=True
        ).select_related(
            'class_obj',
            'class_obj__academic_year',
            'membership',
            'membership__user'
        )
        
        # Filter by class_id if provided
        class_id = self.request.query_params.get('class_id')
        if class_id:
            queryset = queryset.filter(class_obj_id=class_id)
        
        return queryset
    
    @extend_schema(
        summary="O'qituvchining o'quvchilari",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
            OpenApiParameter('class_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StudentClassView(generics.RetrieveAPIView):
    """O'quvchining sinfi."""
    
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = StudentClassSerializer
    
    def get_object(self):
        """O'quvchining sinfini qaytaradi."""
        user = self.request.user
        
        # JWT dan branch_id olish
        branch_id = None
        if hasattr(self.request, 'auth') and isinstance(self.request.auth, dict):
            branch_id = self.request.auth.get('br')
        
        if not branch_id:
            branch_id = self.request.META.get('HTTP_X_BRANCH_ID') or self.request.query_params.get('branch_id')
        
        if not branch_id:
            from rest_framework.exceptions import NotFound
            raise NotFound('Filial topilmadi.')
        
        # O'quvchi membership
        student_membership = get_object_or_404(
            BranchMembership,
            user=user,
            branch_id=branch_id,
            role='student',
            deleted_at__isnull=True
        )
        
        # O'quvchining sinfi
        class_student = ClassStudent.objects.filter(
            membership=student_membership,
            deleted_at__isnull=True,
            is_active=True
        ).select_related(
            'class_obj',
            'class_obj__branch',
            'class_obj__academic_year',
            'class_obj__class_teacher',
            'class_obj__class_teacher__user',
            'class_obj__room'
        ).prefetch_related(
            'class_obj__class_subjects__subject',
            'class_obj__class_subjects__teacher',
            'class_obj__class_subjects__teacher__user',
            'class_obj__class_subjects__quarter'
        ).first()
        
        if not class_student:
            from rest_framework.exceptions import NotFound
            raise NotFound('O\'quvchi sinfga biriktirilmagan.')
        
        return class_student.class_obj
    
    @extend_schema(
        summary="O'quvchining sinfi",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class StudentSubjectsView(generics.ListAPIView):
    """O'quvchining fanlari."""
    
    permission_classes = [IsAuthenticated, IsStudent]
    serializer_class = StudentSubjectSerializer
    
    def get_queryset(self):
        """O'quvchining fanlarini qaytaradi."""
        user = self.request.user
        
        # JWT dan branch_id olish
        branch_id = None
        if hasattr(self.request, 'auth') and isinstance(self.request.auth, dict):
            branch_id = self.request.auth.get('br')
        
        if not branch_id:
            branch_id = self.request.META.get('HTTP_X_BRANCH_ID') or self.request.query_params.get('branch_id')
        
        if not branch_id:
            return ClassSubject.objects.none()
        
        # O'quvchi membership
        student_membership = get_object_or_404(
            BranchMembership,
            user=user,
            branch_id=branch_id,
            role='student',
            deleted_at__isnull=True
        )
        
        # O'quvchining sinfi
        class_student = ClassStudent.objects.filter(
            membership=student_membership,
            deleted_at__isnull=True,
            is_active=True
        ).first()
        
        if not class_student:
            return ClassSubject.objects.none()
        
        # O'quvchining sinfidagi fanlari
        queryset = ClassSubject.objects.filter(
            class_obj=class_student.class_obj,
            deleted_at__isnull=True,
            is_active=True
        ).select_related(
            'subject',
            'teacher',
            'teacher__user',
            'quarter'
        )
        
        return queryset
    
    @extend_schema(
        summary="O'quvchining fanlari",
        parameters=[
            OpenApiParameter('branch_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

