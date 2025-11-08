from __future__ import annotations

from django.urls import path
from .views import MyProfileView, MyBranchProfileView


urlpatterns = [
    path("me/", MyProfileView.as_view(), name="profile-me"),
    path("branch/<uuid:branch_id>/", MyBranchProfileView.as_view(), name="profile-branch-me"),
]
