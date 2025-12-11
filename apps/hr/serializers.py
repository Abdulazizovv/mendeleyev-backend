"""HR API serializers."""

from rest_framework import serializers
from apps.hr.models import StaffRole, StaffProfile, BalanceTransaction, SalaryPayment
from apps.hr.choices import (
    EmploymentType, StaffStatus, TransactionType, 
    PaymentMethod, PaymentStatus
)
from django.contrib.auth import get_user_model

User = get_user_model()


class StaffRoleSerializer(serializers.ModelSerializer):
    """Serializer for StaffRole."""
    
    staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffRole
        fields = [
            'id', 'name', 'code', 'branch', 'permissions',
            'salary_range_min', 'salary_range_max', 'description',
            'is_active', 'staff_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'staff_count']
    
    def get_staff_count(self, obj):
        return obj.staff_members.filter(deleted_at__isnull=True, status='active').count()
    
    def validate(self, data):
        """Validate salary range."""
        min_salary = data.get('salary_range_min')
        max_salary = data.get('salary_range_max')
        
        if min_salary and max_salary and min_salary > max_salary:
            raise serializers.ValidationError({
                'salary_range_min': 'Minimal maosh maksimal maoshdan katta bo\'lishi mumkin emas.'
            })
        
        return data


class StaffRoleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffRole
        fields = [
            'id', 'name', 'code', 'branch', 'branch_name',
            'is_active', 'staff_count'
        ]
    
    def get_staff_count(self, obj):
        return obj.staff_members.filter(deleted_at__isnull=True, status='active').count()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = fields


class StaffProfileSerializer(serializers.ModelSerializer):
    """Serializer for StaffProfile."""
    
    user_info = UserBasicSerializer(source='user', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    staff_role_info = StaffRoleListSerializer(source='staff_role', read_only=True)
    balance_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'user_info', 'branch', 'branch_name',
            'membership', 'staff_role', 'staff_role_info',
            'employment_type', 'hire_date', 'termination_date',
            'base_salary', 'current_balance', 'balance_summary',
            'bank_account', 'tax_id', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_info', 'branch_name', 'staff_role_info',
            'current_balance', 'balance_summary', 'created_at', 'updated_at'
        ]
    
    def get_balance_summary(self, obj):
        """Get balance summary using service."""
        from apps.hr.services import BalanceService
        return BalanceService.get_balance_summary(obj)


class StaffProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    role_name = serializers.CharField(source='staff_role.name', read_only=True)
    
    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'user_name', 'branch', 'branch_name',
            'staff_role', 'role_name', 'employment_type',
            'base_salary', 'current_balance', 'status', 'hire_date'
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.phone_number


class StaffProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff profile."""
    
    class Meta:
        model = StaffProfile
        fields = [
            'user', 'branch', 'membership', 'staff_role',
            'employment_type', 'hire_date', 'base_salary',
            'bank_account', 'tax_id', 'notes'
        ]
    
    def validate(self, data):
        """Validate unique user-branch combination."""
        user = data.get('user')
        branch = data.get('branch')
        
        if StaffProfile.objects.filter(
            user=user,
            branch=branch,
            deleted_at__isnull=True
        ).exists():
            raise serializers.ValidationError({
                'user': 'Bu foydalanuvchi uchun bu filialda allaqachon xodim profili mavjud.'
            })
        
        return data


class BalanceTransactionSerializer(serializers.ModelSerializer):
    """Serializer for BalanceTransaction."""
    
    staff_name = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    processed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BalanceTransaction
        fields = [
            'id', 'staff', 'staff_name', 'transaction_type',
            'transaction_type_display', 'amount', 'previous_balance',
            'new_balance', 'reference', 'description', 'salary_payment',
            'processed_by', 'processed_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'staff_name', 'transaction_type_display',
            'previous_balance', 'new_balance', 'processed_by_name', 'created_at'
        ]
    
    def get_staff_name(self, obj):
        return obj.staff.user.get_full_name() or obj.staff.user.phone_number
    
    def get_processed_by_name(self, obj):
        if obj.processed_by:
            return obj.processed_by.get_full_name() or obj.processed_by.phone_number
        return None


class BalanceTransactionCreateSerializer(serializers.Serializer):
    """Serializer for creating balance transaction via service."""
    
    transaction_type = serializers.ChoiceField(choices=TransactionType.choices)
    amount = serializers.IntegerField(min_value=1)
    description = serializers.CharField()
    reference = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        """Create transaction via BalanceService."""
        from apps.hr.services import BalanceService
        
        staff = self.context['staff']
        processed_by = self.context['request'].user
        
        return BalanceService.apply_transaction(
            staff=staff,
            transaction_type=validated_data['transaction_type'],
            amount=validated_data['amount'],
            description=validated_data['description'],
            reference=validated_data.get('reference', ''),
            processed_by=processed_by,
        )


class SalaryPaymentSerializer(serializers.ModelSerializer):
    """Serializer for SalaryPayment."""
    
    staff_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display',
        read_only=True
    )
    processed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'staff', 'staff_name', 'month', 'amount',
            'payment_date', 'payment_method', 'payment_method_display',
            'status', 'status_display', 'notes', 'reference_number',
            'processed_by', 'processed_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'staff_name', 'status_display', 'payment_method_display',
            'processed_by_name', 'created_at', 'updated_at'
        ]
    
    def get_staff_name(self, obj):
        return obj.staff.user.get_full_name() or obj.staff.user.phone_number
    
    def get_processed_by_name(self, obj):
        if obj.processed_by:
            return obj.processed_by.get_full_name() or obj.processed_by.phone_number
        return None


class SalaryPaymentBulkSerializer(serializers.Serializer):
    """Serializer for bulk salary payments."""
    
    staff_id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)
    payment_date = serializers.DateField()
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_staff_id(self, value):
        """Validate staff exists."""
        try:
            StaffProfile.objects.get(pk=value, deleted_at__isnull=True)
        except StaffProfile.DoesNotExist:
            raise serializers.ValidationError(f'Xodim ID {value} topilmadi.')
        return value


class SalaryReportSerializer(serializers.Serializer):
    """Serializer for salary report."""
    
    month = serializers.DateField()
    total_staff = serializers.IntegerField()
    total_paid = serializers.IntegerField()
    total_amount = serializers.IntegerField()
    by_role = serializers.ListField()
    by_status = serializers.DictField()
