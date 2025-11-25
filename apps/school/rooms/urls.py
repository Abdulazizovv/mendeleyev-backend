from django.urls import path
from .views import (
    BuildingListView,
    BuildingDetailView,
    RoomListView,
    RoomDetailView,
)

app_name = 'rooms'

urlpatterns = [
    # Buildings
    path('branches/<uuid:branch_id>/buildings/', BuildingListView.as_view(), name='building-list'),
    path('branches/<uuid:branch_id>/buildings/<uuid:id>/', BuildingDetailView.as_view(), name='building-detail'),
    
    # Rooms
    path('branches/<uuid:branch_id>/rooms/', RoomListView.as_view(), name='room-list'),
    path('branches/<uuid:branch_id>/rooms/<uuid:id>/', RoomDetailView.as_view(), name='room-detail'),
]

