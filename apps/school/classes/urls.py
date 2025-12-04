from django.urls import path
from .views import (
    ClassListView,
    ClassDetailView,
    ClassStudentListView,
    ClassStudentDetailView,
    ClassAvailableStudentsView,
    ClassStudentTransferView,
)

app_name = 'classes'

urlpatterns = [
    # Classes
    path('branches/<uuid:branch_id>/classes/', ClassListView.as_view(), name='class-list'),
    path('branches/<uuid:branch_id>/classes/<uuid:id>/', ClassDetailView.as_view(), name='class-detail'),
    
    # Class Students
    path('classes/<uuid:class_id>/students/', ClassStudentListView.as_view(), name='class-student-list'),
    path('classes/<uuid:class_id>/students/<uuid:student_id>/', ClassStudentDetailView.as_view(), name='class-student-detail'),
    path('classes/<uuid:class_id>/students/<uuid:student_id>/transfer/', ClassStudentTransferView.as_view(), name='class-student-transfer'),
    # Available students for class
    path('branches/<uuid:branch_id>/classes/<uuid:class_id>/available-students/', ClassAvailableStudentsView.as_view(), name='class-available-students'),
]

