"""Views for attendance module."""
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from apps.common.permissions import HasBranchRole
from apps.common.mixins import AuditTrailMixin
from .models import (
    LessonAttendance, StudentAttendanceRecord, AttendanceStatistics,
    AttendanceStatus
)
from .serializers import (
    LessonAttendanceSerializer, LessonAttendanceCreateSerializer,
    StudentAttendanceRecordSerializer, StudentAttendanceRecordCreateSerializer,
    BulkAttendanceMarkSerializer, AttendanceStatisticsSerializer,
    AttendanceLockSerializer
)


# ========== Lesson Attendance Views ==========

class LessonAttendanceListView(AuditTrailMixin, generics.ListCreateAPIView):
    """
    List and create lesson attendances.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['class_subject', 'date', 'lesson_number', 'is_locked']
    ordering_fields = ['date', 'lesson_number', 'created_at']
    ordering = ['-date', '-lesson_number']
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return LessonAttendance.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'class_subject', 'class_subject__class_obj',
            'class_subject__subject', 'class_subject__teacher',
            'lesson'
        ).prefetch_related('records')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LessonAttendanceCreateSerializer
        return LessonAttendanceSerializer
    
    def get_permissions(self):
        """Teachers and admins can view/create attendance."""
        self.required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
        return super().get_permissions()
    
    @extend_schema(
        summary="List lesson attendances",
        parameters=[
            OpenApiParameter('date', type=str, description='Filter by date (YYYY-MM-DD)'),
            OpenApiParameter('class_subject', type=str, description='Filter by class subject ID'),
            OpenApiParameter('is_locked', type=bool, description='Filter by lock status'),
        ],
        responses={200: LessonAttendanceSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create lesson attendance",
        request=LessonAttendanceCreateSerializer,
        responses={201: LessonAttendanceSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LessonAttendanceDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete lesson attendance.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
    lookup_url_kwarg = 'attendance_id'
    
    def get_queryset(self):
        branch_id = self.kwargs.get('branch_id')
        return LessonAttendance.objects.filter(
            class_subject__class_obj__branch_id=branch_id,
            deleted_at__isnull=True
        ).select_related(
            'class_subject', 'lesson'
        ).prefetch_related('records')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return LessonAttendanceCreateSerializer
        return LessonAttendanceSerializer


# ========== Student Attendance Record Views ==========

class StudentAttendanceRecordListView(AuditTrailMixin, generics.ListCreateAPIView):
    """
    List and create student attendance records.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['attendance', 'student', 'status']
    ordering_fields = ['marked_at', 'created_at']
    ordering = ['-marked_at']
    
    def get_queryset(self):
        attendance_id = self.kwargs.get('attendance_id')
        return StudentAttendanceRecord.objects.filter(
            attendance_id=attendance_id,
            deleted_at__isnull=True
        ).select_related('student', 'student__membership__user', 'attendance')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudentAttendanceRecordCreateSerializer
        return StudentAttendanceRecordSerializer


class StudentAttendanceRecordDetailView(AuditTrailMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a student attendance record.
    """
    permission_classes = [IsAuthenticated, HasBranchRole]
    required_branch_roles = ('branch_admin', 'teacher', 'super_admin')
    lookup_url_kwarg = 'record_id'
    
    def get_queryset(self):
        attendance_id = self.kwargs.get('attendance_id')
        return StudentAttendanceRecord.objects.filter(
            attendance_id=attendance_id,
            deleted_at__isnull=True
        ).select_related('student', 'attendance')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return StudentAttendanceRecordCreateSerializer
        return StudentAttendanceRecordSerializer


# ========== Bulk Attendance Marking ==========

@extend_schema(
    summary="Bulk mark attendance",
    description="Mark attendance for multiple students in one request",
    request=BulkAttendanceMarkSerializer,
    responses={200: LessonAttendanceSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def bulk_mark_attendance(request, branch_id):
    """Bulk mark attendance for multiple students."""
    # Check permissions
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
    
    serializer = BulkAttendanceMarkSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    attendance = serializer.save()
    
    result_serializer = LessonAttendanceSerializer(attendance)
    return Response(result_serializer.data)


# ========== Attendance Statistics ==========

@extend_schema(
    summary="Get attendance statistics for a student",
    parameters=[
        OpenApiParameter('student_id', type=str, required=True),
        OpenApiParameter('start_date', type=str, description='YYYY-MM-DD'),
        OpenApiParameter('end_date', type=str, description='YYYY-MM-DD'),
        OpenApiParameter('class_subject_id', type=str, description='Filter by subject'),
    ],
    responses={200: AttendanceStatisticsSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBranchRole])
def student_attendance_statistics(request, branch_id):
    """Get attendance statistics for a student."""
    from auth.profiles.models import StudentProfile
    from apps.school.subjects.models import ClassSubject
    from django.db.models import Count, Q
    
    student_id = request.query_params.get('student_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    class_subject_id = request.query_params.get('class_subject_id')
    
    if not student_id:
        return Response(
            {'error': 'student_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate dates
    from datetime import datetime
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get student
    try:
        student = StudentProfile.objects.get(id=student_id)
    except StudentProfile.DoesNotExist:
        return Response(
            {'error': 'Student not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Build query
    query = StudentAttendanceRecord.objects.filter(
        student=student,
        deleted_at__isnull=True
    )
    
    if start_date:
        query = query.filter(attendance__date__gte=start_date)
    if end_date:
        query = query.filter(attendance__date__lte=end_date)
    if class_subject_id:
        query = query.filter(attendance__class_subject_id=class_subject_id)
    
    # Calculate statistics
    stats = query.aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
        absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
        late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
        excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
    )
    
    # Calculate attendance rate
    total = stats['total']
    if total > 0:
        attended = stats['present'] + stats['late'] + stats['excused']
        attendance_rate = round((attended / total) * 100, 2)
    else:
        attendance_rate = 0.00
    
    return Response({
        'student_id': str(student.id),
        'student_name': student.get_full_name() if hasattr(student, 'get_full_name') else str(student),
        'start_date': start_date,
        'end_date': end_date,
        'total_lessons': total,
        'present_count': stats['present'],
        'absent_count': stats['absent'],
        'late_count': stats['late'],
        'excused_count': stats['excused'],
        'attendance_rate': attendance_rate
    })


@extend_schema(
    summary="Get attendance statistics for a class",
    parameters=[
        OpenApiParameter('class_subject_id', type=str, required=True),
        OpenApiParameter('start_date', type=str, description='YYYY-MM-DD'),
        OpenApiParameter('end_date', type=str, description='YYYY-MM-DD'),
    ],
    responses={200: {
        'type': 'object',
        'properties': {
            'class_subject_id': {'type': 'string'},
            'total_lessons': {'type': 'integer'},
            'average_attendance_rate': {'type': 'number'},
            'students': {'type': 'array'}
        }
    }}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBranchRole])
def class_attendance_statistics(request, branch_id):
    """Get attendance statistics for a class subject."""
    from apps.school.subjects.models import ClassSubject
    from apps.school.classes.models import ClassStudent
    
    class_subject_id = request.query_params.get('class_subject_id')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not class_subject_id:
        return Response(
            {'error': 'class_subject_id required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate dates
    from datetime import datetime
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': 'Invalid date format. Use YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get class subject
    try:
        class_subject = ClassSubject.objects.get(id=class_subject_id)
    except ClassSubject.DoesNotExist:
        return Response(
            {'error': 'Class subject not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Get all students in class
    students = ClassStudent.objects.filter(
        class_obj=class_subject.class_obj,
        is_active=True,
        deleted_at__isnull=True
    ).select_related('membership', 'membership__user')
    
    # Calculate stats for each student
    student_stats = []
    total_rate = 0
    count = 0
    
    for class_student in students:
        student_profile = class_student.membership.studentprofile
        
        # Build query
        query = StudentAttendanceRecord.objects.filter(
            student=student_profile,
            attendance__class_subject=class_subject,
            deleted_at__isnull=True
        )
        
        if start_date:
            query = query.filter(attendance__date__gte=start_date)
        if end_date:
            query = query.filter(attendance__date__lte=end_date)
        
        # Calculate statistics
        stats = query.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count('id', filter=Q(status=AttendanceStatus.ABSENT)),
            late=Count('id', filter=Q(status=AttendanceStatus.LATE)),
            excused=Count('id', filter=Q(status=AttendanceStatus.EXCUSED)),
        )
        
        total = stats['total']
        if total > 0:
            attended = stats['present'] + stats['late'] + stats['excused']
            attendance_rate = round((attended / total) * 100, 2)
            total_rate += attendance_rate
            count += 1
        else:
            attendance_rate = 0.00
        
        student_stats.append({
            'student_id': str(student_profile.id),
            'student_name': f"{class_student.membership.user.first_name} {class_student.membership.user.last_name}",
            'total_lessons': total,
            'present_count': stats['present'],
            'absent_count': stats['absent'],
            'late_count': stats['late'],
            'excused_count': stats['excused'],
            'attendance_rate': attendance_rate
        })
    
    # Calculate average attendance rate
    average_rate = round(total_rate / count, 2) if count > 0 else 0.00
    
    # Get total lessons count
    total_lessons = LessonAttendance.objects.filter(
        class_subject=class_subject,
        deleted_at__isnull=True
    )
    if start_date:
        total_lessons = total_lessons.filter(date__gte=start_date)
    if end_date:
        total_lessons = total_lessons.filter(date__lte=end_date)
    total_lessons = total_lessons.count()
    
    return Response({
        'class_subject_id': str(class_subject.id),
        'class_name': class_subject.class_obj.name,
        'subject_name': class_subject.subject.name,
        'total_lessons': total_lessons,
        'average_attendance_rate': average_rate,
        'students': student_stats
    })


# ========== Attendance Locking ==========

@extend_schema(
    summary="Lock or unlock attendances",
    description="Lock attendances to prevent edits or unlock for admin override",
    request=AttendanceLockSerializer,
    responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}, 'affected_count': {'type': 'integer'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBranchRole])
def lock_unlock_attendance(request, branch_id):
    """Lock or unlock attendances."""
    # Only admins can lock/unlock
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
    
    serializer = AttendanceLockSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    attendance_ids = serializer.validated_data['attendance_ids']
    action = serializer.validated_data['action']
    
    attendances = LessonAttendance.objects.filter(
        id__in=attendance_ids,
        deleted_at__isnull=True
    )
    
    affected_count = 0
    for attendance in attendances:
        if action == 'lock':
            if not attendance.is_locked:
                attendance.lock(locked_by=membership)
                affected_count += 1
        else:  # unlock
            if attendance.is_locked:
                attendance.unlock()
                affected_count += 1
    
    return Response({
        'message': f'{affected_count} davomat {action} qilindi',
        'affected_count': affected_count
    })
