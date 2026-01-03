"""URLs for grades module."""
from django.urls import path
from . import views

app_name = 'grades'

urlpatterns = [
    # Assessment Types
    path(
        'branches/<uuid:branch_id>/assessment-types/',
        views.AssessmentTypeListView.as_view(),
        name='assessment-type-list'
    ),
    path(
        'branches/<uuid:branch_id>/assessment-types/<uuid:type_id>/',
        views.AssessmentTypeDetailView.as_view(),
        name='assessment-type-detail'
    ),
    
    # Assessments
    path(
        'branches/<uuid:branch_id>/assessments/',
        views.AssessmentListView.as_view(),
        name='assessment-list'
    ),
    path(
        'branches/<uuid:branch_id>/assessments/<uuid:assessment_id>/',
        views.AssessmentDetailView.as_view(),
        name='assessment-detail'
    ),
    
    # Grades
    path(
        'branches/<uuid:branch_id>/grades/',
        views.GradeListView.as_view(),
        name='grade-list'
    ),
    path(
        'branches/<uuid:branch_id>/grades/<uuid:grade_id>/',
        views.GradeDetailView.as_view(),
        name='grade-detail'
    ),
    
    # Bulk Operations
    path(
        'branches/<uuid:branch_id>/grades/bulk-create/',
        views.bulk_create_grades,
        name='grade-bulk-create'
    ),
    
    # Quarter Grades
    path(
        'branches/<uuid:branch_id>/quarter-grades/',
        views.QuarterGradeListView.as_view(),
        name='quarter-grade-list'
    ),
    path(
        'branches/<uuid:branch_id>/quarter-grades/<uuid:quarter_grade_id>/',
        views.QuarterGradeDetailView.as_view(),
        name='quarter-grade-detail'
    ),
    path(
        'branches/<uuid:branch_id>/quarter-grades/calculate/',
        views.calculate_quarter_grades,
        name='quarter-grade-calculate'
    ),
    
    # Statistics
    path(
        'branches/<uuid:branch_id>/grades/statistics/student/',
        views.student_grade_statistics,
        name='grade-student-statistics'
    ),
    
    # Locking
    path(
        'branches/<uuid:branch_id>/grades/lock-unlock/',
        views.lock_unlock_grades,
        name='grade-lock-unlock'
    ),
]
