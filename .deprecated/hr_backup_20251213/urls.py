"""HR URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.hr.views import (
    StaffRoleViewSet,
    StaffProfileViewSet,
    StaffCreateView,
    StaffCheckView,
    BalanceTransactionViewSet,
    SalaryPaymentViewSet
)

app_name = 'hr'

router = DefaultRouter()
router.register(r'roles', StaffRoleViewSet, basename='staffrole')
router.register(r'staff', StaffProfileViewSet, basename='staffprofile')
router.register(r'transactions', BalanceTransactionViewSet, basename='balancetransaction')
router.register(r'salaries', SalaryPaymentViewSet, basename='salarypayment')

urlpatterns = [
    path('staff/create/', StaffCreateView.as_view(), name='staff-create'),
    path('staff/check-user/', StaffCheckView.as_view(), name='staff-check-user'),
    path('', include(router.urls)),
]
