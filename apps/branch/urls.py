from django.urls import path

from .views import (
    ManagedBranchesView,
    RoleListView,
    RoleDetailView,
    MembershipListView,
    BalanceUpdateView,
    BranchSettingsView,
)

urlpatterns = [
    path("managed/", ManagedBranchesView.as_view(), name="managed-branches"),
    # Role endpoints
    path("<uuid:branch_id>/roles/", RoleListView.as_view(), name="branch-roles-list"),
    path("<uuid:branch_id>/roles/<uuid:id>/", RoleDetailView.as_view(), name="branch-role-detail"),
    # Membership endpoints
    path("<uuid:branch_id>/memberships/", MembershipListView.as_view(), name="branch-memberships-list"),
    path("<uuid:branch_id>/memberships/<uuid:membership_id>/balance/", BalanceUpdateView.as_view(), name="membership-balance-update"),
    # Settings endpoints
    path("<uuid:branch_id>/settings/", BranchSettingsView.as_view(), name="branch-settings"),
]
