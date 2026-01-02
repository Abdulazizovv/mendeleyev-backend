"""
Moliya tizimi uchun filterlar.
"""
import django_filters
from django.db.models import Q
from .models import (
    Transaction,
    Payment,
    StudentSubscription,
    FinanceCategory,
    Discount,
    SubscriptionPlan,
    CashRegister,
    TransactionType,
    TransactionStatus,
    DiscountType,
    SubscriptionPeriod,
)


class TransactionFilter(django_filters.FilterSet):
    """Transaction filter."""
    
    # Amount range filters
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    # Date range filters
    date_from = django_filters.DateFilter(field_name='transaction_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='transaction_date', lookup_expr='lte')
    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Multi-value filters
    transaction_type = django_filters.MultipleChoiceFilter(
        choices=TransactionType.choices,
        lookup_expr='in'
    )
    status = django_filters.MultipleChoiceFilter(
        choices=TransactionStatus.choices,
        lookup_expr='in'
    )
    
    # Related object filters
    cash_register = django_filters.UUIDFilter(field_name='cash_register_id')
    category = django_filters.UUIDFilter(field_name='category_id')
    student_profile = django_filters.UUIDFilter(field_name='student_profile_id')
    employee_membership = django_filters.UUIDFilter(field_name='employee_membership_id')
    branch = django_filters.UUIDFilter(field_name='branch_id')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Transaction
        fields = {
            'transaction_type': ['exact', 'in'],
            'status': ['exact', 'in'],
            'payment_method': ['exact'],
            'amount': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'transaction_date': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'gte', 'lte'],
        }
    
    def filter_search(self, queryset, name, value):
        """Search by description, reference_number, student name."""
        return queryset.filter(
            Q(description__icontains=value) |
            Q(reference_number__icontains=value) |
            Q(student_profile__personal_number__icontains=value) |
            Q(student_profile__user_branch__user__first_name__icontains=value) |
            Q(student_profile__user_branch__user__last_name__icontains=value)
        ).distinct()


class PaymentFilter(django_filters.FilterSet):
    """Payment filter."""
    
    # Amount range filters
    base_amount_min = django_filters.NumberFilter(field_name='base_amount', lookup_expr='gte')
    base_amount_max = django_filters.NumberFilter(field_name='base_amount', lookup_expr='lte')
    final_amount_min = django_filters.NumberFilter(field_name='final_amount', lookup_expr='gte')
    final_amount_max = django_filters.NumberFilter(field_name='final_amount', lookup_expr='lte')
    discount_amount_min = django_filters.NumberFilter(field_name='discount_amount', lookup_expr='gte')
    discount_amount_max = django_filters.NumberFilter(field_name='discount_amount', lookup_expr='lte')
    
    # Date range filters
    payment_date_from = django_filters.DateFilter(field_name='payment_date', lookup_expr='gte')
    payment_date_to = django_filters.DateFilter(field_name='payment_date', lookup_expr='lte')
    created_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Period filters
    period_start_from = django_filters.DateFilter(field_name='period_start', lookup_expr='gte')
    period_start_to = django_filters.DateFilter(field_name='period_start', lookup_expr='lte')
    period_end_from = django_filters.DateFilter(field_name='period_end', lookup_expr='gte')
    period_end_to = django_filters.DateFilter(field_name='period_end', lookup_expr='lte')
    
    # Multi-value filter
    period = django_filters.MultipleChoiceFilter(
        choices=SubscriptionPeriod.choices,
        lookup_expr='in'
    )
    
    # Related object filters
    student_profile = django_filters.UUIDFilter(field_name='student_profile_id')
    subscription_plan = django_filters.UUIDFilter(field_name='subscription_plan_id')
    discount = django_filters.UUIDFilter(field_name='discount_id')
    transaction = django_filters.UUIDFilter(field_name='transaction_id')
    branch = django_filters.UUIDFilter(field_name='branch_id')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Payment
        fields = {
            'base_amount': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'final_amount': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'payment_date': ['exact', 'gte', 'lte'],
            'created_at': ['exact', 'gte', 'lte'],
            'period': ['exact', 'in'],
        }
    
    def filter_search(self, queryset, name, value):
        """Search by student info or notes."""
        return queryset.filter(
            Q(notes__icontains=value) |
            Q(student_profile__personal_number__icontains=value) |
            Q(student_profile__user_branch__user__first_name__icontains=value) |
            Q(student_profile__user_branch__user__last_name__icontains=value)
        ).distinct()


class StudentSubscriptionFilter(django_filters.FilterSet):
    """StudentSubscription filter."""
    
    # Debt range filters
    total_debt_min = django_filters.NumberFilter(field_name='total_debt', lookup_expr='gte')
    total_debt_max = django_filters.NumberFilter(field_name='total_debt', lookup_expr='lte')
    
    # Date filters
    next_payment_date_from = django_filters.DateFilter(field_name='next_payment_date', lookup_expr='gte')
    next_payment_date_to = django_filters.DateFilter(field_name='next_payment_date', lookup_expr='lte')
    start_date_from = django_filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_to = django_filters.DateFilter(field_name='start_date', lookup_expr='lte')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter(field_name='is_active')
    
    # Related object filters
    student_profile = django_filters.UUIDFilter(field_name='student_profile_id')
    subscription_plan = django_filters.UUIDFilter(field_name='subscription_plan_id')
    branch = django_filters.UUIDFilter(field_name='branch_id')
    
    # Has debt filter
    has_debt = django_filters.BooleanFilter(method='filter_has_debt')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = StudentSubscription
        fields = {
            'is_active': ['exact'],
            'total_debt': ['exact', 'gte', 'lte', 'gt', 'lt'],
            'next_payment_date': ['exact', 'gte', 'lte'],
            'start_date': ['exact', 'gte', 'lte'],
        }
    
    def filter_has_debt(self, queryset, name, value):
        """Filter subscriptions with debt."""
        if value:
            return queryset.filter(total_debt__gt=0)
        return queryset.filter(total_debt=0)
    
    def filter_search(self, queryset, name, value):
        """Search by student info or subscription plan."""
        return queryset.filter(
            Q(student_profile__personal_number__icontains=value) |
            Q(student_profile__user_branch__user__first_name__icontains=value) |
            Q(student_profile__user_branch__user__last_name__icontains=value) |
            Q(subscription_plan__name__icontains=value)
        ).distinct()


class FinanceCategoryFilter(django_filters.FilterSet):
    """FinanceCategory filter."""
    
    # Type filter
    type = django_filters.ChoiceFilter(choices=[('income', 'Kirim'), ('expense', 'Chiqim')])
    
    # Boolean filters
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_global = django_filters.BooleanFilter(method='filter_is_global')
    has_subcategories = django_filters.BooleanFilter(method='filter_has_subcategories')
    
    # Related object filters
    branch = django_filters.UUIDFilter(field_name='branch_id')
    parent = django_filters.UUIDFilter(field_name='parent_id')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = FinanceCategory
        fields = {
            'type': ['exact'],
            'is_active': ['exact'],
        }
    
    def filter_is_global(self, queryset, name, value):
        """Filter global categories (no branch)."""
        if value:
            return queryset.filter(branch__isnull=True)
        return queryset.filter(branch__isnull=False)
    
    def filter_has_subcategories(self, queryset, name, value):
        """Filter categories with subcategories."""
        if value:
            return queryset.filter(subcategories__isnull=False).distinct()
        return queryset.filter(subcategories__isnull=True)
    
    def filter_search(self, queryset, name, value):
        """Search by name, code, or description."""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(code__icontains=value) |
            Q(description__icontains=value)
        ).distinct()


class DiscountFilter(django_filters.FilterSet):
    """Discount filter."""
    
    # Type filter
    discount_type = django_filters.ChoiceFilter(
        field_name='discount_type',
        choices=DiscountType.choices
    )
    
    # Amount range filters
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    # Date range filters
    valid_from = django_filters.DateFilter(field_name='valid_from', lookup_expr='gte')
    valid_until = django_filters.DateFilter(field_name='valid_until', lookup_expr='lte')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_global = django_filters.BooleanFilter(method='filter_is_global')
    is_valid_now = django_filters.BooleanFilter(method='filter_is_valid_now')
    
    # Related object filters
    branch = django_filters.UUIDFilter(field_name='branch_id')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Discount
        fields = {
            'discount_type': ['exact'],
            'is_active': ['exact'],
            'amount': ['exact', 'gte', 'lte'],
        }
    
    def filter_is_global(self, queryset, name, value):
        """Filter global discounts (no branch)."""
        if value:
            return queryset.filter(branch__isnull=True)
        return queryset.filter(branch__isnull=False)
    
    def filter_is_valid_now(self, queryset, name, value):
        """Filter discounts valid at current time."""
        from django.utils import timezone
        now = timezone.now().date()
        
        if value:
            return queryset.filter(
                is_active=True,
                valid_from__lte=now,
                valid_until__gte=now
            )
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search by name or description."""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        ).distinct()


class SubscriptionPlanFilter(django_filters.FilterSet):
    """SubscriptionPlan filter."""
    
    # Period filter
    period = django_filters.MultipleChoiceFilter(
        choices=SubscriptionPeriod.choices,
        lookup_expr='in'
    )
    
    # Price range filters
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    # Grade level filters
    grade_level_min = django_filters.NumberFilter(field_name='grade_level_min', lookup_expr='gte')
    grade_level_max = django_filters.NumberFilter(field_name='grade_level_max', lookup_expr='lte')
    grade_level = django_filters.NumberFilter(method='filter_grade_level')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter(field_name='is_active')
    is_global = django_filters.BooleanFilter(method='filter_is_global')
    
    # Related object filters
    branch = django_filters.UUIDFilter(field_name='branch_id')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = SubscriptionPlan
        fields = {
            'period': ['exact', 'in'],
            'price': ['exact', 'gte', 'lte'],
            'is_active': ['exact'],
            'grade_level_min': ['exact', 'gte', 'lte'],
            'grade_level_max': ['exact', 'gte', 'lte'],
        }
    
    def filter_is_global(self, queryset, name, value):
        """Filter global plans (no branch)."""
        if value:
            return queryset.filter(branch__isnull=True)
        return queryset.filter(branch__isnull=False)
    
    def filter_grade_level(self, queryset, name, value):
        """Filter plans applicable to a specific grade level."""
        return queryset.filter(
            grade_level_min__lte=value,
            grade_level_max__gte=value
        )
    
    def filter_search(self, queryset, name, value):
        """Search by name or description."""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        ).distinct()


class CashRegisterFilter(django_filters.FilterSet):
    """CashRegister filter."""
    
    # Balance range filters
    balance_min = django_filters.NumberFilter(field_name='balance', lookup_expr='gte')
    balance_max = django_filters.NumberFilter(field_name='balance', lookup_expr='lte')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter(field_name='is_active')
    has_balance = django_filters.BooleanFilter(method='filter_has_balance')
    
    # Related object filters
    branch = django_filters.UUIDFilter(field_name='branch_id')
    
    # Search filter
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = CashRegister
        fields = {
            'is_active': ['exact'],
            'balance': ['exact', 'gte', 'lte', 'gt', 'lt'],
        }
    
    def filter_has_balance(self, queryset, name, value):
        """Filter cash registers with balance."""
        if value:
            return queryset.filter(balance__gt=0)
        return queryset.filter(balance=0)
    
    def filter_search(self, queryset, name, value):
        """Search by name or description."""
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        ).distinct()
