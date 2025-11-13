from django.urls import path

from .views import ManagedBranchesView

urlpatterns = [
    path("managed/", ManagedBranchesView.as_view(), name="managed-branches"),
]
