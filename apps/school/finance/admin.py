"""
Moliya tizimi admin konfiguratsiyasi.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    CashRegister,
    Transaction,
    StudentBalance,
    SubscriptionPlan,
    Discount,
    Payment,
    TransactionType,
    TransactionStatus,
)


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    """Kassa admin."""
    list_display = [
        'name',
        'branch_display',
        'balance_display',
        'is_active',
        'location',
        'created_at',
    ]
    list_filter = ['is_active', 'branch', 'created_at']
    search_fields = ['name', 'description', 'location', 'branch__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'balance']
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'branch', 'name', 'description', 'location')
        }),
        ('Balans', {
            'fields': ('balance',)
        }),
        ('Holat', {
            'fields': ('is_active',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        return obj.branch.name
    branch_display.short_description = 'Filial'
    
    def balance_display(self, obj):
        """Balans ko'rinishi."""
        return f"{obj.balance:,.0f} so'm"
    balance_display.short_description = 'Balans'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Tranzaksiya admin."""
    list_display = [
        'transaction_type_display',
        'amount_display',
        'branch_display',
        'cash_register_display',
        'status_display',
        'payment_method_display',
        'student_display',
        'employee_display',
        'transaction_date',
    ]
    list_filter = [
        'transaction_type',
        'status',
        'payment_method',
        'branch',
        'cash_register',
        'transaction_date',
    ]
    search_fields = [
        'description',
        'reference_number',
        'student_profile__personal_number',
        'employee_membership__user__phone_number',
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'transaction_date'
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'branch', 'cash_register', 'transaction_type', 'status')
        }),
        ('Summa', {
            'fields': ('amount', 'payment_method')
        }),
        ('Ma\'lumotlar', {
            'fields': ('description', 'reference_number', 'transaction_date')
        }),
        ('Bog\'lanishlar', {
            'fields': ('student_profile', 'employee_membership')
        }),
        ('Qo\'shimcha', {
            'fields': ('metadata',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def transaction_type_display(self, obj):
        """Tranzaksiya turi ko'rinishi."""
        return obj.get_transaction_type_display()
    transaction_type_display.short_description = 'Turi'
    
    def amount_display(self, obj):
        """Summa ko'rinishi."""
        return f"{obj.amount:,.0f} so'm"
    amount_display.short_description = 'Summa'
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        return obj.branch.name
    branch_display.short_description = 'Filial'
    
    def cash_register_display(self, obj):
        """Kassa ko'rinishi."""
        return obj.cash_register.name
    cash_register_display.short_description = 'Kassa'
    
    def status_display(self, obj):
        """Holat ko'rinishi."""
        colors = {
            TransactionStatus.PENDING: 'orange',
            TransactionStatus.COMPLETED: 'green',
            TransactionStatus.CANCELLED: 'red',
            TransactionStatus.FAILED: 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Holat'
    
    def payment_method_display(self, obj):
        """To'lov usuli ko'rinishi."""
        return obj.get_payment_method_display()
    payment_method_display.short_description = 'To\'lov usuli'
    
    def student_display(self, obj):
        """O'quvchi ko'rinishi."""
        if obj.student_profile:
            return obj.student_profile.personal_number
        return '-'
    student_display.short_description = 'O\'quvchi'
    
    def employee_display(self, obj):
        """Xodim ko'rinishi."""
        if obj.employee_membership:
            return str(obj.employee_membership.user)
        return '-'
    employee_display.short_description = 'Xodim'


@admin.register(StudentBalance)
class StudentBalanceAdmin(admin.ModelAdmin):
    """O'quvchi balansi admin."""
    list_display = [
        'personal_number_display',
        'student_display',
        'branch_display',
        'balance_display',
        'updated_at',
    ]
    list_filter = [
        'student_profile__user_branch__branch',
        'student_profile__status',
        'created_at',
        'updated_at',
    ]
    search_fields = [
        'student_profile__personal_number',
        'student_profile__user_branch__user__first_name',
        'student_profile__user_branch__user__last_name',
        'student_profile__user_branch__user__phone_number',
    ]
    autocomplete_fields = ['student_profile']
    readonly_fields = ['id', 'created_at', 'updated_at', 'balance']
    date_hierarchy = 'updated_at'
    list_per_page = 50
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'student_profile', 'balance')
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'student_profile',
            'student_profile__user_branch',
            'student_profile__user_branch__user',
            'student_profile__user_branch__branch'
        )
    
    def student_display(self, obj):
        """O'quvchi ko'rinishi."""
        return obj.student_profile.full_name or obj.student_profile.user_branch.user.phone_number
    student_display.short_description = 'O\'quvchi'
    
    def personal_number_display(self, obj):
        """Shaxsiy raqam ko'rinishi."""
        if obj.student_profile.personal_number:
            return format_html(
                '<strong style="color:#0066cc;">{}</strong>',
                obj.student_profile.personal_number
            )
        return '-'
    personal_number_display.short_description = 'Shaxsiy raqam'
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        return obj.student_profile.user_branch.branch.name if obj.student_profile.user_branch.branch else '-'
    branch_display.short_description = 'Filial'
    
    def balance_display(self, obj):
        """Balans ko'rinishi."""
        if obj.balance > 0:
            return format_html(
                '<span style="color:#090; font-weight: bold;">{:,} so\'m</span>',
                obj.balance
            )
        elif obj.balance < 0:
            return format_html(
                '<span style="color:#f00; font-weight: bold;">{:,} so\'m</span>',
                obj.balance
            )
        return format_html('<span style="color:#999;">0 so\'m</span>')
    balance_display.short_description = 'Balans'


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Abonement tarifi admin."""
    list_display = [
        'name',
        'branch_display',
        'grade_level_range',
        'period_display',
        'price_display',
        'is_active_badge',
        'created_at',
    ]
    list_filter = ['is_active', 'period', 'branch', 'created_at']
    search_fields = ['name', 'description', 'branch__name']
    autocomplete_fields = ['branch']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_per_page = 50
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'branch', 'name', 'description')
        }),
        ('Sinf darajasi', {
            'fields': ('grade_level_min', 'grade_level_max')
        }),
        ('Narx', {
            'fields': ('period', 'price')
        }),
        ('Holat', {
            'fields': ('is_active',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        return obj.branch.name
    branch_display.short_description = 'Filial'
    
    def grade_level_range(self, obj):
        """Sinf darajasi diapazoni."""
        return f"{obj.grade_level_min}-{obj.grade_level_max}"
    grade_level_range.short_description = 'Sinf darajasi'
    
    def period_display(self, obj):
        """Davr ko'rinishi."""
        return obj.get_period_display()
    period_display.short_description = 'Davr'
    
    def price_display(self, obj):
        """Narx ko'rinishi."""
        return format_html(
            '<strong style="color:#0066cc;">{:,} so\'m</strong>',
            obj.price
        )
    price_display.short_description = 'Narx'
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        if obj.branch:
            return obj.branch.name
        return format_html('<span style="color:#999; font-style: italic;">Umumiy (barcha filiallar)</span>')
    branch_display.short_description = 'Filial'
    
    @admin.display(description='Holat', boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">✓ Faol</span>')
        return format_html('<span style="color:#999;">✗ Nofaol</span>')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    """Chegirma admin."""
    list_display = [
        'name',
        'branch_display',
        'discount_type_display',
        'amount_display',
        'is_active_badge',
        'valid_from',
        'valid_until',
        'is_valid_badge',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'discount_type',
        'branch',
        'valid_from',
        'valid_until',
        'created_at',
    ]
    search_fields = ['name', 'description', 'branch__name']
    autocomplete_fields = ['branch']
    readonly_fields = ['id', 'created_at', 'updated_at', 'is_valid_display']
    date_hierarchy = 'valid_from'
    list_per_page = 50
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'branch', 'name', 'description')
        }),
        ('Chegirma', {
            'fields': ('discount_type', 'amount')
        }),
        ('Holat', {
            'fields': ('is_active',)
        }),
        ('Sana cheklovlari', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Qo\'shimcha shartlar', {
            'fields': ('conditions',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        return obj.branch.name
    branch_display.short_description = 'Filial'
    
    def discount_type_display(self, obj):
        """Chegirma turi ko'rinishi."""
        return obj.get_discount_type_display()
    discount_type_display.short_description = 'Turi'
    
    def amount_display(self, obj):
        """Summa ko'rinishi."""
        if obj.discount_type == 'percentage':
            return format_html(
                '<strong style="color:#0066cc;">{}%</strong>',
                obj.amount
            )
        return format_html(
            '<strong style="color:#0066cc;">{:,} so\'m</strong>',
            obj.amount
        )
    amount_display.short_description = 'Summa/Foiz'
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        if obj.branch:
            return obj.branch.name
        return format_html('<span style="color:#999; font-style: italic;">Umumiy (barcha filiallar)</span>')
    branch_display.short_description = 'Filial'
    
    @admin.display(description='Holat', boolean=False)
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#090;">✓ Faol</span>')
        return format_html('<span style="color:#999;">✗ Nofaol</span>')
    
    @admin.display(description='Amal qiladi', boolean=False)
    def is_valid_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color:#090;">✓ Ha</span>')
        return format_html('<span style="color:#f00;">✗ Yo\'q</span>')
    
    @admin.display(description='Amal qiladi')
    def is_valid_display(self, obj):
        return obj.is_valid


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """To'lov admin."""
    list_display = [
        'personal_number_display',
        'student_display',
        'branch_display',
        'subscription_plan_display',
        'final_amount_display',
        'discount_display',
        'payment_method_display',
        'period_display',
        'payment_date',
        'created_at',
    ]
    list_filter = [
        'payment_method',
        'period',
        'branch',
        'payment_date',
        'period_start',
        'period_end',
        'created_at',
    ]
    search_fields = [
        'student_profile__personal_number',
        'student_profile__user_branch__user__first_name',
        'student_profile__user_branch__user__last_name',
        'student_profile__user_branch__user__phone_number',
        'notes',
    ]
    autocomplete_fields = ['student_profile', 'branch', 'subscription_plan', 'discount', 'transaction']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    list_per_page = 50
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('id', 'student_profile', 'branch', 'subscription_plan')
        }),
        ('Summa', {
            'fields': ('base_amount', 'discount', 'discount_amount', 'final_amount')
        }),
        ('To\'lov', {
            'fields': ('payment_method', 'period', 'payment_date')
        }),
        ('Davr', {
            'fields': ('period_start', 'period_end')
        }),
        ('Tranzaksiya', {
            'fields': ('transaction',)
        }),
        ('Qo\'shimcha', {
            'fields': ('notes',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def student_display(self, obj):
        """O'quvchi ko'rinishi."""
        return obj.student_profile.full_name or obj.student_profile.user_branch.user.phone_number
    student_display.short_description = 'O\'quvchi'
    
    def personal_number_display(self, obj):
        """Shaxsiy raqam ko'rinishi."""
        if obj.student_profile.personal_number:
            return format_html(
                '<strong style="color:#0066cc;">{}</strong>',
                obj.student_profile.personal_number
            )
        return '-'
    personal_number_display.short_description = 'Shaxsiy raqam'
    
    def branch_display(self, obj):
        """Filial ko'rinishi."""
        return obj.branch.name
    branch_display.short_description = 'Filial'
    
    def subscription_plan_display(self, obj):
        """Abonement tarifi ko'rinishi."""
        if obj.subscription_plan:
            return str(obj.subscription_plan)
        return '-'
    subscription_plan_display.short_description = 'Abonement tarifi'
    
    def final_amount_display(self, obj):
        """Yakuniy summa ko'rinishi."""
        return format_html(
            '<strong style="color:#0066cc;">{:,} so\'m</strong>',
            obj.final_amount
        )
    final_amount_display.short_description = 'Yakuniy summa'
    
    def discount_display(self, obj):
        """Chegirma ko'rinishi."""
        if obj.discount:
            return str(obj.discount)
        if obj.discount_amount > 0:
            return f"{obj.discount_amount:,.0f} so'm"
        return '-'
    discount_display.short_description = 'Chegirma'
    
    def payment_method_display(self, obj):
        """To'lov usuli ko'rinishi."""
        return obj.get_payment_method_display()
    payment_method_display.short_description = 'To\'lov usuli'
    
    def period_display(self, obj):
        """Davr ko'rinishi."""
        return obj.get_period_display()
    period_display.short_description = 'Davr'

