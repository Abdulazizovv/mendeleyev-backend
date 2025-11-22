from django.urls import path
from .views import (
    AcademicYearListView,
    AcademicYearDetailView,
    QuarterListView,
    CurrentAcademicYearView,
)

app_name = 'academic'

urlpatterns = [
    # Academic Years
    path('branches/<uuid:branch_id>/academic-years/', AcademicYearListView.as_view(), name='academic-year-list'),
    path('branches/<uuid:branch_id>/academic-years/<uuid:id>/', AcademicYearDetailView.as_view(), name='academic-year-detail'),
    
    # Quarters
    path('academic-years/<uuid:academic_year_id>/quarters/', QuarterListView.as_view(), name='quarter-list'),
    
    # Current
    path('branches/<uuid:branch_id>/academic-years/current/', CurrentAcademicYearView.as_view(), name='current-academic-year'),
]

