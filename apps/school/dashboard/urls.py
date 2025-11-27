from django.urls import path
from .views import (
    TeacherClassesView,
    TeacherSubjectsView,
    TeacherStudentsView,
    StudentClassView,
    StudentSubjectsView,
)

app_name = 'dashboard'

urlpatterns = [
    # Teacher dashboard
    path('teacher/classes/', TeacherClassesView.as_view(), name='teacher-classes'),
    path('teacher/subjects/', TeacherSubjectsView.as_view(), name='teacher-subjects'),
    path('teacher/students/', TeacherStudentsView.as_view(), name='teacher-students'),
    
    # Student dashboard
    path('student/class/', StudentClassView.as_view(), name='student-class'),
    path('student/subjects/', StudentSubjectsView.as_view(), name='student-subjects'),
]

