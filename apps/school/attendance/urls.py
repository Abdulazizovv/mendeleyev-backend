"""URLs for attendance module."""
from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # Lesson Attendance
    path(
        'branches/<uuid:branch_id>/attendance/',
        views.LessonAttendanceListView.as_view(),
        name='attendance-list'
    ),
    path(
        'branches/<uuid:branch_id>/attendance/<uuid:attendance_id>/',
        views.LessonAttendanceDetailView.as_view(),
        name='attendance-detail'
    ),
    
    # Student Attendance Records
    path(
        'branches/<uuid:branch_id>/attendance/<uuid:attendance_id>/records/',
        views.StudentAttendanceRecordListView.as_view(),
        name='attendance-record-list'
    ),
    path(
        'branches/<uuid:branch_id>/attendance/<uuid:attendance_id>/records/<uuid:record_id>/',
        views.StudentAttendanceRecordDetailView.as_view(),
        name='attendance-record-detail'
    ),
    
    # Bulk Operations
    path(
        'branches/<uuid:branch_id>/attendance/bulk-mark/',
        views.bulk_mark_attendance,
        name='attendance-bulk-mark'
    ),
    
    # Attendance Locking
    path(
        'branches/<uuid:branch_id>/attendance/lock-unlock/',
        views.lock_unlock_attendance,
        name='attendance-lock-unlock'
    ),
    
    # Statistics
    path(
        'branches/<uuid:branch_id>/attendance/statistics/student/',
        views.student_attendance_statistics,
        name='attendance-student-statistics'
    ),
    path(
        'branches/<uuid:branch_id>/attendance/statistics/class/',
        views.class_attendance_statistics,
        name='attendance-class-statistics'
    ),
]
