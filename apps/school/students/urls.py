from django.urls import path
from .views import (
    StudentCreateView,
    StudentListView,
    StudentDetailView,
    StudentDocumentsUpdateView,
    StudentRelativeListView,
    StudentRelativeUpdateView,
    UserCheckView,
    StudentRelativeCheckView,
)

app_name = 'students'

urlpatterns = [
    path('', StudentListView.as_view(), name='student-list'),
    path('create/', StudentCreateView.as_view(), name='student-create'),
    path('check-user/', UserCheckView.as_view(), name='user-check'),
    path('check-relative/', StudentRelativeCheckView.as_view(), name='relative-check'),
    path('<uuid:student_id>/', StudentDetailView.as_view(), name='student-detail'),
    path('<uuid:student_id>/documents/', StudentDocumentsUpdateView.as_view(), name='student-documents-update'),
    path('<uuid:student_id>/relatives/', StudentRelativeListView.as_view(), name='student-relatives'),
    path('<uuid:student_id>/relatives/<uuid:relative_id>/', StudentRelativeUpdateView.as_view(), name='student-relative-update-delete'),
]

