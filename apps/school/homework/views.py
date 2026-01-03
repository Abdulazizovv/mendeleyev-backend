from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Case, When, IntegerField
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Homework, HomeworkSubmission, HomeworkStatus, SubmissionStatus
from .serializers import (
    HomeworkListSerializer,
    HomeworkDetailSerializer,
    HomeworkCreateSerializer,
    HomeworkUpdateSerializer,
    SubmissionListSerializer,
    SubmissionDetailSerializer,
    SubmissionCreateSerializer,
    SubmissionGradeSerializer,
    BulkGradeSerializer,
    StudentHomeworkStatisticsSerializer,
    ClassHomeworkStatisticsSerializer
)
from apps.school.subjects.models import ClassSubject
from apps.school.classes.models import ClassStudent
from auth.profiles.models import StudentProfile


class HomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework.
    
    Teachers can create homework for their classes.
    Students can view homework assigned to their classes.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get homework based on user role."""
        user = self.request.user
        branch_role = self.request.auth.get('branch_role') if self.request.auth else None
        
        queryset = Homework.objects.filter(deleted_at__isnull=True)
        
        if branch_role == 'admin':
            # Admins see all homework in their branch
            queryset = queryset.filter(
                class_subject__class_obj__branch=user.current_branch
            )
        elif branch_role == 'teacher':
            # Teachers see homework for their subjects
            queryset = queryset.filter(
                class_subject__teacher__membership__user=user,
                class_subject__teacher__membership__is_active=True
            )
        elif branch_role == 'student':
            # Students see homework for their classes
            student_profile = getattr(user, 'student_profile', None)
            if student_profile:
                class_students = ClassStudent.objects.filter(
                    membership=student_profile.membership,
                    is_active=True,
                    deleted_at__isnull=True
                ).values_list('class_obj_id', flat=True)
                
                queryset = queryset.filter(
                    class_subject__class_obj_id__in=class_students
                )
            else:
                queryset = queryset.none()
        else:
            queryset = queryset.none()
        
        # Filter by query params
        class_subject_id = self.request.query_params.get('class_subject')
        if class_subject_id:
            queryset = queryset.filter(class_subject_id=class_subject_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related(
            'class_subject__class_obj',
            'class_subject__subject',
            'class_subject__teacher__membership__user',
            'lesson',
            'assessment'
        ).order_by('-due_date', '-assigned_date')
    
    def get_serializer_class(self):
        """Get serializer based on action."""
        if self.action == 'list':
            return HomeworkListSerializer
        elif self.action in ['create']:
            return HomeworkCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return HomeworkUpdateSerializer
        return HomeworkDetailSerializer
    
    def perform_create(self, serializer):
        """Create homework."""
        # Verify teacher has access to class_subject
        class_subject = serializer.validated_data['class_subject']
        user = self.request.user
        branch_role = self.request.auth.get('branch_role') if self.request.auth else None
        
        if branch_role != 'admin':
            # Check teacher owns this class_subject
            if not ClassSubject.objects.filter(
                id=class_subject.id,
                teacher__membership__user=user,
                deleted_at__isnull=True
            ).exists():
                raise serializers.ValidationError(
                    'Sizda ushbu sinf fani uchun vazifa yaratish huquqi yo\'q.'
                )
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close homework (no more submissions accepted)."""
        homework = self.get_object()
        homework.status = HomeworkStatus.CLOSED
        homework.save()
        
        serializer = self.get_serializer(homework)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen homework (accept submissions again)."""
        homework = self.get_object()
        homework.status = HomeworkStatus.ACTIVE
        homework.save()
        
        serializer = self.get_serializer(homework)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get all submissions for this homework."""
        homework = self.get_object()
        submissions = HomeworkSubmission.objects.filter(
            homework=homework,
            deleted_at__isnull=True
        ).select_related(
            'student__membership__user'
        ).order_by('-submitted_at', 'student__membership__user__last_name')
        
        serializer = SubmissionListSerializer(submissions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for this homework."""
        homework = self.get_object()
        
        submissions = HomeworkSubmission.objects.filter(
            homework=homework,
            deleted_at__isnull=True
        )
        
        total_students = ClassStudent.objects.filter(
            class_obj=homework.class_subject.class_obj,
            is_active=True,
            deleted_at__isnull=True
        ).count()
        
        submitted_count = submissions.filter(
            status__in=[SubmissionStatus.SUBMITTED, SubmissionStatus.GRADED, SubmissionStatus.LATE]
        ).count()
        
        graded_count = submissions.filter(
            status=SubmissionStatus.GRADED
        ).count()
        
        late_count = submissions.filter(is_late=True).count()
        
        average_score = submissions.filter(
            status=SubmissionStatus.GRADED,
            score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        completion_rate = (submitted_count / total_students * 100) if total_students > 0 else 0
        
        return Response({
            'total_students': total_students,
            'submitted': submitted_count,
            'not_submitted': total_students - submitted_count,
            'graded': graded_count,
            'late': late_count,
            'average_score': round(average_score, 2),
            'completion_rate': round(completion_rate, 2)
        })


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework submissions.
    
    Students submit homework.
    Teachers grade submissions.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get submissions based on user role."""
        user = self.request.user
        branch_role = self.request.auth.get('branch_role') if self.request.auth else None
        
        queryset = HomeworkSubmission.objects.filter(deleted_at__isnull=True)
        
        if branch_role == 'admin':
            # Admins see all submissions in their branch
            queryset = queryset.filter(
                homework__class_subject__class_obj__branch=user.current_branch
            )
        elif branch_role == 'teacher':
            # Teachers see submissions for their subjects
            queryset = queryset.filter(
                homework__class_subject__teacher__membership__user=user
            )
        elif branch_role == 'student':
            # Students see only their own submissions
            student_profile = getattr(user, 'student_profile', None)
            if student_profile:
                queryset = queryset.filter(student=student_profile)
            else:
                queryset = queryset.none()
        else:
            queryset = queryset.none()
        
        # Filter by query params
        homework_id = self.request.query_params.get('homework')
        if homework_id:
            queryset = queryset.filter(homework_id=homework_id)
        
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.select_related(
            'homework',
            'student__membership__user'
        ).order_by('-submitted_at', '-created_at')
    
    def get_serializer_class(self):
        """Get serializer based on action."""
        if self.action == 'list':
            return SubmissionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SubmissionCreateSerializer
        elif self.action == 'grade':
            return SubmissionGradeSerializer
        return SubmissionDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create or update submission."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        
        output_serializer = SubmissionDetailSerializer(submission)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        """Grade a submission."""
        submission = self.get_object()
        serializer = self.get_serializer(submission, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        output_serializer = SubmissionDetailSerializer(submission)
        return Response(output_serializer.data)
    
    @action(detail=True, methods=['post'])
    def return_for_revision(self, request, pk=None):
        """Return submission for revision."""
        submission = self.get_object()
        feedback = request.data.get('teacher_feedback')
        
        if not feedback:
            return Response(
                {'error': 'teacher_feedback kerak.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        submission.return_for_revision(feedback)
        
        serializer = SubmissionDetailSerializer(submission)
        return Response(serializer.data)


# Statistics views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_homework_statistics(request):
    """Get homework statistics for a student."""
    student_id = request.query_params.get('student_id')
    quarter_id = request.query_params.get('quarter_id')
    
    if not student_id:
        return Response(
            {'error': 'student_id kerak.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    student = get_object_or_404(StudentProfile, id=student_id, deleted_at__isnull=True)
    
    # Get student's classes
    class_students = ClassStudent.objects.filter(
        membership=student.membership,
        is_active=True,
        deleted_at__isnull=True
    ).values_list('class_obj_id', flat=True)
    
    # Get homework for student's classes
    homework_qs = Homework.objects.filter(
        class_subject__class_obj_id__in=class_students,
        deleted_at__isnull=True
    )
    
    if quarter_id:
        # Filter by quarter date range
        from apps.school.quarters.models import Quarter
        quarter = get_object_or_404(Quarter, id=quarter_id, deleted_at__isnull=True)
        homework_qs = homework_qs.filter(
            assigned_date__gte=quarter.start_date,
            assigned_date__lte=quarter.end_date
        )
    
    total_homework = homework_qs.count()
    
    # Get submissions
    submissions = HomeworkSubmission.objects.filter(
        student=student,
        homework__in=homework_qs,
        deleted_at__isnull=True
    )
    
    submitted = submissions.filter(
        status__in=[SubmissionStatus.SUBMITTED, SubmissionStatus.GRADED, SubmissionStatus.LATE]
    ).count()
    
    not_submitted = total_homework - submitted
    late = submissions.filter(is_late=True).count()
    graded = submissions.filter(status=SubmissionStatus.GRADED).count()
    
    average_score = submissions.filter(
        status=SubmissionStatus.GRADED,
        score__isnull=False
    ).aggregate(avg=Avg('score'))['avg'] or 0
    
    completion_rate = (submitted / total_homework * 100) if total_homework > 0 else 0
    
    data = {
        'total_homework': total_homework,
        'submitted': submitted,
        'not_submitted': not_submitted,
        'late': late,
        'graded': graded,
        'average_score': round(average_score, 2),
        'completion_rate': round(completion_rate, 2)
    }
    
    serializer = StudentHomeworkStatisticsSerializer(data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def class_homework_statistics(request):
    """Get homework statistics for a class."""
    class_id = request.query_params.get('class_id')
    quarter_id = request.query_params.get('quarter_id')
    
    if not class_id:
        return Response(
            {'error': 'class_id kerak.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    homework_qs = Homework.objects.filter(
        class_subject__class_obj_id=class_id,
        deleted_at__isnull=True
    )
    
    if quarter_id:
        from apps.school.quarters.models import Quarter
        quarter = get_object_or_404(Quarter, id=quarter_id, deleted_at__isnull=True)
        homework_qs = homework_qs.filter(
            assigned_date__gte=quarter.start_date,
            assigned_date__lte=quarter.end_date
        )
    
    total_homework = homework_qs.count()
    active_homework = homework_qs.filter(status=HomeworkStatus.ACTIVE).count()
    closed_homework = homework_qs.filter(status=HomeworkStatus.CLOSED).count()
    
    # Get all submissions for this class's homework
    submissions = HomeworkSubmission.objects.filter(
        homework__in=homework_qs,
        deleted_at__isnull=True
    )
    
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(status=SubmissionStatus.GRADED).count()
    
    # Calculate average completion rate across all homework
    completion_rates = []
    for homework in homework_qs:
        completion_rates.append(homework.get_completion_rate())
    
    average_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
    
    # Calculate average score
    average_score = submissions.filter(
        status=SubmissionStatus.GRADED,
        score__isnull=False
    ).aggregate(avg=Avg('score'))['avg'] or 0
    
    data = {
        'total_homework': total_homework,
        'active_homework': active_homework,
        'closed_homework': closed_homework,
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'average_completion_rate': round(average_completion_rate, 2),
        'average_score': round(average_score, 2)
    }
    
    serializer = ClassHomeworkStatisticsSerializer(data)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_grade_submissions(request):
    """Bulk grade multiple submissions."""
    serializer = BulkGradeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    result = serializer.save()
    
    return Response(result, status=status.HTTP_200_OK)
