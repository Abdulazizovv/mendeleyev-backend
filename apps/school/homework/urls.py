from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HomeworkViewSet,
    SubmissionViewSet,
    student_homework_statistics,
    class_homework_statistics,
    bulk_grade_submissions
)

router = DefaultRouter()
router.register(r'homework', HomeworkViewSet, basename='homework')
router.register(r'submissions', SubmissionViewSet, basename='submission')

urlpatterns = [
    path('', include(router.urls)),
    
    # Statistics endpoints
    path(
        'statistics/student/',
        student_homework_statistics,
        name='student-homework-statistics'
    ),
    path(
        'statistics/class/',
        class_homework_statistics,
        name='class-homework-statistics'
    ),
    
    # Bulk operations
    path(
        'submissions/bulk-grade/',
        bulk_grade_submissions,
        name='bulk-grade-submissions'
    ),
]
