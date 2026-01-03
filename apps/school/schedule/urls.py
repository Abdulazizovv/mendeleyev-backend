"""URLs for schedule module."""
from django.urls import path
from . import views

app_name = 'schedule'

urlpatterns = [
    # Timetable Templates
    path(
        'branches/<uuid:branch_id>/timetables/',
        views.TimetableTemplateListView.as_view(),
        name='timetable-list'
    ),
    path(
        'branches/<uuid:branch_id>/timetables/<uuid:template_id>/',
        views.TimetableTemplateDetailView.as_view(),
        name='timetable-detail'
    ),
    
    # Timetable Slots
    path(
        'branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/',
        views.TimetableSlotListView.as_view(),
        name='slot-list'
    ),
    path(
        'branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/<uuid:slot_id>/',
        views.TimetableSlotDetailView.as_view(),
        name='slot-detail'
    ),
    path(
        'branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/bulk-create/',
        views.bulk_create_slots,
        name='slot-bulk-create'
    ),
    path(
        'branches/<uuid:branch_id>/timetables/<uuid:template_id>/check-conflicts/',
        views.check_slot_conflicts,
        name='slot-check-conflicts'
    ),
    path(
        'branches/<uuid:branch_id>/timetables/<uuid:template_id>/slots/<uuid:slot_id>/check-conflicts/',
        views.check_slot_conflicts,
        name='slot-check-conflicts-detail'
    ),
    
    # Lesson Topics
    path(
        'branches/<uuid:branch_id>/lesson-topics/',
        views.LessonTopicListView.as_view(),
        name='lesson-topic-list'
    ),
    path(
        'branches/<uuid:branch_id>/lesson-topics/<uuid:topic_id>/',
        views.LessonTopicDetailView.as_view(),
        name='lesson-topic-detail'
    ),
    
    # Lesson Instances
    path(
        'branches/<uuid:branch_id>/lessons/',
        views.LessonInstanceListView.as_view(),
        name='lesson-list'
    ),
    path(
        'branches/<uuid:branch_id>/lessons/<uuid:lesson_id>/',
        views.LessonInstanceDetailView.as_view(),
        name='lesson-detail'
    ),
    
    # Lesson Generation
    path(
        'branches/<uuid:branch_id>/lessons/generate/',
        views.generate_lessons,
        name='lesson-generate'
    ),
    
    # Weekly Schedule
    path(
        'branches/<uuid:branch_id>/schedule/weekly/',
        views.weekly_schedule,
        name='weekly-schedule'
    ),
]
