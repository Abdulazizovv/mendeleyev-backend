"""Views for grades module."""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Avg, Count

from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import AssessmentType, Assessment, Grade, QuarterGrade
from .serializers import (
    AssessmentTypeSerializer, AssessmentTypeCreateSerializer,
    AssessmentSerializer, AssessmentCreateSerializer,
    GradeSerializer, GradeCreateSerializer, GradeUpdateSerializer,
    BulkGradeCreateSerializer, QuarterGradeSerializer,
    QuarterGradeUpdateSerializer, GradeLockSerializer
)


# ========== Assessment Type Views ==========

class AssessmentTypeListView(AuditTrailMixin, generics.ListCreateAPIView):
    """List and create assessment types."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return AssessmentType.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssessmentTypeCreateSerializer
        return AssessmentTypeSerializer


class AssessmentTypeDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete assessment type."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'super_admin')
    lookup_url_kwarg = 'type_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return AssessmentType.objects.filter(
            branch_id=branch_id,
            deleted_at__isnull=True
        )
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssessmentTypeCreateSerializer
        return AssessmentTypeSerializer


# ========== Assessment Views ==========

class AssessmentListView(AuditTrailMixin, generics.ListCreateAPIView):
    """List and create assessments."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['class_subject', 'assessment_type', 'quarter', 'date', 'is_locked']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'created_at']
    ordering = ['-date']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return Assessment.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'class_subject', 'class_subject__class_obj',
            'class_subject__subject', 'assessment_type', 'quarter'
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssessmentCreateSerializer
        return AssessmentSerializer
    
    def get_permissions(self):
        """Teachers and admins can view/create."""
        self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        return super().get_permissions()


class AssessmentDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete assessment."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
    lookup_url_kwarg = 'assessment_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return Assessment.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('class_subject', 'assessment_type', 'quarter')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssessmentCreateSerializer
        return AssessmentSerializer


# ========== Grade Views ==========

class GradeListView(AuditTrailMixin, generics.ListCreateAPIView):
    """List and create grades."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['assessment', 'student']
    ordering_fields = ['graded_at', 'score']
    ordering = ['-graded_at']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return Grade.objects.filter(
            assessment__class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('assessment', 'student', 'student__membership__user')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GradeCreateSerializer
        return GradeSerializer


class GradeDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete grade."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
    lookup_url_kwarg = 'grade_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return Grade.objects.filter(
            assessment__class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('assessment', 'student')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GradeUpdateSerializer
        return GradeSerializer


# ========== Bulk Grading ==========

@extend_schema(
    summary="Bulk create grades",
    description="Create or update grades for multiple students in one request",
    request=BulkGradeCreateSerializer,
    responses={200: GradeSerializer(many=True)}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def bulk_create_grades(request, branch_id):
    """Bulk create or update grades."""
    if not hasattr(request.user, 'branch_memberships'):
        return Response(
            {'error': 'User has no branch memberships'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    membership = request.user.branch_memberships.filter(
        branch_id=branch_id,
        role__in=['branch_admin', 'teacher', 'super_admin']
    ).first()
    
    if not membership:
        return Response(
            {'error': 'Permission denied. Teacher or admin role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = BulkGradeCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    grades = serializer.save()
    
    result_serializer = GradeSerializer(grades, many=True)
    return Response(result_serializer.data)


# ========== Quarter Grade Views ==========

class QuarterGradeListView(generics.ListAPIView):
    """List quarter grades."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'student', 'super_admin')
    serializer_class = QuarterGradeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['student', 'class_subject', 'quarter', 'is_locked']
    ordering_fields = ['last_calculated', 'final_grade']
    ordering = ['-last_calculated']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return QuarterGrade.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'student', 'student__membership__user',
            'class_subject', 'class_subject__class_obj',
            'class_subject__subject', 'quarter'
        )


class QuarterGradeDetailView(AuditTrailMixin, generics.RetrieveUpdateAPIView):
    """Retrieve or update quarter grade."""
    permission_classes = [IsAuthenticated, HasBranchRole]
    lookup_url_kwarg = 'quarter_grade_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return QuarterGrade.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related('student', 'class_subject', 'quarter')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return QuarterGradeUpdateSerializer
        return QuarterGradeSerializer
    
    def get_permissions(self):
        """Only admins can update quarter grades."""
        if self.request.method in ['PUT', 'PATCH']:
            self.required_branch_roles = ('branch_admin', 'super_admin')
        else:
            self.required_branch_roles = ('branch_admin', 'teacher', 'student', 'super_admin')
        return super().get_permissions()


# ========== Calculate Quarter Grades ==========

@extend_schema(
    summary="Calculate quarter grades",
    description="Calculate quarter grades for students in a class subject",
    parameters=[
        OpenApiParameter('class_subject_id', type=str, required=True),
        OpenApiParameter('quarter_id', type=str, required=True),
    ],
    responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}, 'calculated_count': {'type': 'integer'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def calculate_quarter_grades(request, branch_id):
    """Calculate quarter grades for all students in a class subject."""
    from apps.school.subjects.models import ClassSubject
    from apps.school.academic.models import Quarter
    from apps.school.classes.models import ClassStudent
    from auth.profiles.models import StudentProfile
    
    # Only admins and teachers can calculate
    if not hasattr(request.user, 'branch_memberships'):
        return Response(
            {'error': 'User has no branch memberships'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    membership = request.user.branch_memberships.filter(
        branch_id=branch_id,
        role__in=['branch_admin', 'teacher', 'super_admin']
    ).first()
    
    if not membership:
        return Response(
            {'error': 'Permission denied. Teacher or admin role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    class_subject_id = request.data.get('class_subject_id')
    quarter_id = request.data.get('quarter_id')
    
    if not class_subject_id or not quarter_id:
        return Response(
            {'error': 'class_subject_id and quarter_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        class_subject = ClassSubject.objects.get(id=class_subject_id)
        quarter = Quarter.objects.get(id=quarter_id)
    except (ClassSubject.DoesNotExist, Quarter.DoesNotExist):
        return Response(
            {'error': 'Class subject or quarter not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all students in class
    students = ClassStudent.objects.filter(
        class_obj=class_subject.class_obj,
        is_active=True,
        deleted_at__isnull=True
    ).select_related('membership')
    
    calculated_count = 0
    
    for class_student in students:
        student_profile = class_student.membership.studentprofile
        
        # Get or create quarter grade
        quarter_grade, created = QuarterGrade.objects.get_or_create(
            student=student_profile,
            class_subject=class_subject,
            quarter=quarter,
            defaults={'calculated_grade': 0}
        )
        
        # Calculate
        quarter_grade.calculate()
        calculated_count += 1
    
    return Response({
        'message': f'{calculated_count} o\'quvchi uchun chorak baholari hisoblandi',
        'calculated_count': calculated_count
    })


# ========== Grade Statistics ==========

@extend_schema(
    summary="Get grade statistics for a student",
    parameters=[
        OpenApiParameter('student_id', type=str, required=True),
        OpenApiParameter('class_subject_id', type=str, description='Filter by subject'),
        OpenApiParameter('quarter_id', type=str, description='Filter by quarter'),
    ],
    responses={200: {'type': 'object'}}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBranchRole])
def student_grade_statistics(request, branch_id):
    """Get grade statistics for a student."""
    from auth.profiles.models import StudentProfile
    
    student_id = request.query_params.get('student_id')
    class_subject_id = request.query_params.get('class_subject_id')
    quarter_id = request.query_params.get('quarter_id')
    
    if not student_id:
        return Response(
            {'error': 'student_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        student = StudentProfile.objects.get(id=student_id)
    except StudentProfile.DoesNotExist:
        return Response(
            {'error': 'Student not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Build query
    query = Grade.objects.filter(
        student=student,
        deleted_at__isnull=True
    )
    
    if class_subject_id:
        query = query.filter(assessment__class_subject_id=class_subject_id)
    if quarter_id:
        query = query.filter(assessment__quarter_id=quarter_id)
    
    # Calculate statistics
    stats = query.aggregate(
        total_grades=Count('id'),
        average_score=Avg('final_score'),
        average_percentage=Avg('score') * 100 / Avg('assessment__max_score') if query.exists() else 0
    )
    
    # Get quarter grades
    quarter_grades_query = QuarterGrade.objects.filter(
        student=student,
        deleted_at__isnull=True
    )
    
    if class_subject_id:
        quarter_grades_query = quarter_grades_query.filter(class_subject_id=class_subject_id)
    if quarter_id:
        quarter_grades_query = quarter_grades_query.filter(quarter_id=quarter_id)
    
    quarter_grades = QuarterGradeSerializer(quarter_grades_query, many=True).data
    
    return Response({
        'student_id': str(student.id),
        'student_name': student.get_full_name() if hasattr(student, 'get_full_name') else str(student),
        'total_grades': stats['total_grades'],
        'average_score': round(stats['average_score'] or 0, 2),
        'quarter_grades': quarter_grades
    })


# ========== Locking ==========

@extend_schema(
    summary="Lock or unlock assessments/quarter grades",
    request=GradeLockSerializer,
    responses={200: {'type': 'object'}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def lock_unlock_grades(request, branch_id):
    """Lock or unlock assessments or quarter grades."""
    # Only admins
    if not hasattr(request.user, 'branch_memberships'):
        return Response(
            {'error': 'User has no branch memberships'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    membership = request.user.branch_memberships.filter(
        branch_id=branch_id,
        role__in=['branch_admin', 'super_admin']
    ).first()
    
    if not membership:
        return Response(
            {'error': 'Permission denied. Admin role required.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = GradeLockSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    ids = serializer.validated_data['ids']
    action = serializer.validated_data['action']
    lock_type = serializer.validated_data['type']
    
    affected_count = 0
    
    if lock_type == 'assessment':
        assessments = Assessment.objects.filter(
            id__in=ids,
            deleted_at__isnull=True
        )
        
        for assessment in assessments:
            if action == 'lock':
                if not assessment.is_locked:
                    assessment.lock()
                    affected_count += 1
            else:
                if assessment.is_locked:
                    assessment.unlock()
                    affected_count += 1
    
    elif lock_type == 'quarter_grade':
        quarter_grades = QuarterGrade.objects.filter(
            id__in=ids,
            deleted_at__isnull=True
        )
        
        for qg in quarter_grades:
            if action == 'lock':
                if not qg.is_locked:
                    qg.lock()
                    affected_count += 1
            else:
                if qg.is_locked:
                    qg.unlock()
                    affected_count += 1
    
    return Response({
        'message': f'{affected_count} {lock_type} {action} qilindi',
        'affected_count': affected_count
    })
