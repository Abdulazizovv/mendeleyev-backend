"""
Moliya tizimi URL konfiguratsiyasi.
"""
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Cash Registers
    path('cash-registers/', views.CashRegisterListView.as_view(), name='cash-register-list'),
    path('cash-registers/<uuid:pk>/', views.CashRegisterDetailView.as_view(), name='cash-register-detail'),
    
    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    
    # Student Balances
    path('student-balances/', views.StudentBalanceListView.as_view(), name='student-balance-list'),
    path('student-balances/<uuid:pk>/', views.StudentBalanceDetailView.as_view(), name='student-balance-detail'),
    
    # Subscription Plans
    path('subscription-plans/', views.SubscriptionPlanListView.as_view(), name='subscription-plan-list'),
    path('subscription-plans/<uuid:pk>/', views.SubscriptionPlanDetailView.as_view(), name='subscription-plan-detail'),
    
    # Discounts
    path('discounts/', views.DiscountListView.as_view(), name='discount-list'),
    path('discounts/<uuid:pk>/', views.DiscountDetailView.as_view(), name='discount-detail'),
    
    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    
    # Statistics
    path('statistics/', views.FinanceStatisticsView.as_view(), name='statistics'),
]

