"""HR admin configuration."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from apps.hr.models import StaffRole, StaffProfile, BalanceTransaction, SalaryPayment


@admin.register(StaffRole)
class StaffRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'salary_range_display', 'is_active', 'staff_count')
    list_filter = ('branch', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('branch', 'name', 'code', 'description', 'is_active')
        }),
        (_('Ruxsatlar'), {
            'fields': ('permissions',)
        }),
        (_('Maosh diapazoni'), {
            'fields': ('salary_range_min', 'salary_range_max'),
            'classes': ('collapse',),
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    @admin.display(description=_('Maosh diapazoni'))
    def salary_range_display(self, obj):
        if obj.salary_range_min and obj.salary_range_max:
            return f"{obj.salary_range_min:_} - {obj.salary_range_max:_} so'm"
        elif obj.salary_range_min:
            return f"Min: {obj.salary_range_min:_} so'm"
        elif obj.salary_range_max:
            return f"Max: {obj.salary_range_max:_} so'm"
        return "-"
    
    @admin.display(description=_('Xodimlar soni'))
    def staff_count(self, obj):
        return obj.staff_members.filter(deleted_at__isnull=True).count()


class BalanceTransactionInline(admin.TabularInline):
    model = BalanceTransaction
    extra = 0
    can_delete = False
    readonly_fields = ('transaction_type', 'amount', 'previous_balance', 'new_balance', 'description', 'created_at')
    fields = ('transaction_type', 'amount', 'previous_balance', 'new_balance', 'description', 'created_at')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_display', 'branch', 'staff_role', 'employment_type', 
        'base_salary_display', 'balance_display', 'status', 'hire_date'
    )
    list_filter = ('branch', 'staff_role', 'employment_type', 'status', 'hire_date')
    search_fields = ('user__first_name', 'user__last_name', 'user__phone_number', 'tax_id', 'bank_account')
    readonly_fields = ('current_balance', 'created_at', 'updated_at', 'deleted_at')
    autocomplete_fields = ('user', 'branch', 'staff_role', 'membership')
    inlines = [BalanceTransactionInline]
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('user', 'branch', 'membership', 'staff_role', 'employment_type', 'status')
        }),
        (_('Ish ma\'lumotlari'), {
            'fields': ('hire_date', 'termination_date')
        }),
        (_('Moliyaviy ma\'lumotlar'), {
            'fields': ('base_salary', 'current_balance', 'bank_account', 'tax_id')
        }),
        (_('Qo\'shimcha'), {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    @admin.display(description=_('Xodim'))
    def user_display(self, obj):
        name = obj.user.get_full_name() or obj.user.phone_number
        return format_html('<strong>{}</strong>', name)
    
    @admin.display(description=_('Asosiy maosh'))
    def base_salary_display(self, obj):
        return f"{obj.base_salary:_} so'm"
    
    @admin.display(description=_('Balans'))
    def balance_display(self, obj):
        color = '#090' if obj.current_balance >= 0 else '#d9534f'
        return format_html(
            '<span style="color:{};">{} so\'m</span>',
            color,
            f"{obj.current_balance:_}"
        )


@admin.register(BalanceTransaction)
class BalanceTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'staff_display', 'transaction_type', 'amount_display', 
        'balance_change', 'reference', 'created_at'
    )
    list_filter = ('transaction_type', 'created_at', 'staff__branch')
    search_fields = ('staff__user__first_name', 'staff__user__last_name', 'reference', 'description')
    readonly_fields = (
        'staff', 'transaction_type', 'amount', 'previous_balance', 
        'new_balance', 'reference', 'description', 'processed_by', 
        'salary_payment', 'created_at', 'updated_at'
    )
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('staff', 'transaction_type', 'amount')
        }),
        (_('Balans'), {
            'fields': ('previous_balance', 'new_balance')
        }),
        (_('Qo\'shimcha'), {
            'fields': ('reference', 'description', 'salary_payment', 'processed_by')
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    @admin.display(description=_('Xodim'))
    def staff_display(self, obj):
        return obj.staff.user.get_full_name() or obj.staff.user.phone_number
    
    @admin.display(description=_('Summa'))
    def amount_display(self, obj):
        return f"{obj.amount:_} so'm"
    
    @admin.display(description=_('Balans o\'zgarishi'))
    def balance_change(self, obj):
        change = obj.new_balance - obj.previous_balance
        color = '#090' if change >= 0 else '#d9534f'
        sign = '+' if change >= 0 else ''
        return format_html(
            '<span style="color:{};">{}{}</span>',
            color,
            sign,
            f"{change:_}"
        )


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'staff_display', 'month', 'amount_display', 'payment_date', 
        'payment_method', 'status_badge'
    )
    list_filter = ('status', 'payment_method', 'payment_date', 'staff__branch')
    search_fields = ('staff__user__first_name', 'staff__user__last_name', 'reference_number')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    autocomplete_fields = ('staff', 'processed_by')
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        (_('Asosiy ma\'lumotlar'), {
            'fields': ('staff', 'month', 'amount', 'status')
        }),
        (_('To\'lov ma\'lumotlari'), {
            'fields': ('payment_date', 'payment_method', 'reference_number')
        }),
        (_('Qo\'shimcha'), {
            'fields': ('notes', 'processed_by'),
            'classes': ('collapse',),
        }),
        (_('Tizim ma\'lumotlari'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    @admin.display(description=_('Xodim'))
    def staff_display(self, obj):
        return obj.staff.user.get_full_name() or obj.staff.user.phone_number
    
    @admin.display(description=_('Summa'))
    def amount_display(self, obj):
        return format_html('{:,} so\'m', obj.amount)
    
    @admin.display(description=_('Holat'))
    def status_badge(self, obj):
        colors = {
            'pending': '#f0ad4e',
            'paid': '#090',
            'cancelled': '#999',
            'failed': '#d9534f',
        }
        color = colors.get(obj.status, '#999')
        return format_html(
            '<span style="color:{};">{}</span>',
            color,
            obj.get_status_display()
        )
