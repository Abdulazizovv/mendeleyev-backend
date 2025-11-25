from django.urls import path
from .views import (
    SubjectListView,
    SubjectDetailView,
    ClassSubjectListView,
    ClassSubjectDetailView,
)

app_name = 'subjects'

urlpatterns = [
    # Subjects
    path('branches/<uuid:branch_id>/subjects/', SubjectListView.as_view(), name='subject-list'),
    path('branches/<uuid:branch_id>/subjects/<uuid:id>/', SubjectDetailView.as_view(), name='subject-detail'),
    
    # Class Subjects
    path('classes/<uuid:class_id>/subjects/', ClassSubjectListView.as_view(), name='class-subject-list'),
    path('classes/<uuid:class_id>/subjects/<uuid:id>/', ClassSubjectDetailView.as_view(), name='class-subject-detail'),
]

