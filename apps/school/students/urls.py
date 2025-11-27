from django.urls import path
from .views import (
    StudentCreateView,
    StudentListView,
    StudentDetailView,
    StudentRelativeListView,
)

app_name = 'students'

urlpatterns = [
    path('', StudentListView.as_view(), name='student-list'),
    path('create/', StudentCreateView.as_view(), name='student-create'),
    path('<uuid:student_id>/', StudentDetailView.as_view(), name='student-detail'),
    path('<uuid:student_id>/relatives/', StudentRelativeListView.as_view(), name='student-relatives'),
]

