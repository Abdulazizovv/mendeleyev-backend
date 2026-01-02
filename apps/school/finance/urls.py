"""
Moliya tizimi URL konfiguratsiyasi.
"""
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Finance Categories
    path('categories/', views.FinanceCategoryListCreateView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', views.FinanceCategoryDetailView.as_view(), name='category-detail'),
    
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
    
    # Student Subscriptions
    path('student-subscriptions/', views.StudentSubscriptionListView.as_view(), name='student-subscription-list'),
    path('student-subscriptions/<uuid:id>/', views.StudentSubscriptionDetailView.as_view(), name='student-subscription-detail'),
    
    # Payment Due Summary
    path('payment-due-summary/', views.PaymentDueSummaryView.as_view(), name='payment-due-summary'),
    
    # Statistics
    path('statistics/', views.FinanceStatisticsView.as_view(), name='statistics'),
    
    # Export
    path('export/transactions/', views.ExportTransactionsView.as_view(), name='export-transactions'),
    path('export/payments/', views.ExportPaymentsView.as_view(), name='export-payments'),
    path('export/task-status/<str:task_id>/', views.ExportTaskStatusView.as_view(), name='export-task-status'),
]

