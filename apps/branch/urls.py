from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ManagedBranchesView,
    RoleListView,
    RoleDetailView,
    MembershipListView,
    BalanceUpdateView,
    BranchSettingsView,
    StaffViewSet,
    BranchSettingsViewSet,
    BalanceTransactionViewSet,
    SalaryPaymentViewSet,
    BranchDashboardStatisticsView,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'staff', StaffViewSet, basename='staff')
router.register(r'settings', BranchSettingsViewSet, basename='branch-settings')
router.register(r'transactions', BalanceTransactionViewSet, basename='balance-transaction')
router.register(r'payments', SalaryPaymentViewSet, basename='salary-payment')

urlpatterns = [
    path("managed/", ManagedBranchesView.as_view(), name="managed-branches"),
    # Dashboard statistics
    path("school/dashboard/statistics/", BranchDashboardStatisticsView.as_view(), name="dashboard-statistics"),
    # Role endpoints
    path("<uuid:branch_id>/roles/", RoleListView.as_view(), name="branch-roles-list"),
    path("<uuid:branch_id>/roles/<uuid:id>/", RoleDetailView.as_view(), name="branch-role-detail"),
    # Membership endpoints
    path("<uuid:branch_id>/memberships/", MembershipListView.as_view(), name="branch-memberships-list"),
    path("<uuid:branch_id>/memberships/<uuid:membership_id>/balance/", BalanceUpdateView.as_view(), name="membership-balance-update"),
    # Settings endpoints
    path("<uuid:branch_id>/settings/", BranchSettingsView.as_view(), name="branch-settings"),
    # Staff endpoints (ViewSet)
    path("", include(router.urls)),
]
