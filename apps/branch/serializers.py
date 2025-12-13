from __future__ import annotations


from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.branch.models import (
    BranchMembership, BalanceTransaction, SalaryPayment,
    Role, BranchRole, EmploymentType
)
from apps.branch.choices import TransactionType, PaymentMethod, PaymentStatus

User = get_user_model()


class StaffSerializer(serializers.ModelSerializer):
    """Unified staff member serializer.
    
    Combines BranchMembership data with user information.
    Used for listing and retrieving staff members.
    """
    
    # User information (read-only for list/retrieve)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Role information
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    role_ref_id = serializers.UUIDField(source='role_ref.id', read_only=True, allow_null=True)
    role_ref_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    
    # Computed fields
    salary = serializers.IntegerField(source='get_salary', read_only=True)
    days_employed = serializers.IntegerField(read_only=True)
    years_employed = serializers.FloatField(read_only=True)
    is_active_employment = serializers.BooleanField(read_only=True)
    balance_status = serializers.CharField(read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    
    class Meta:
        model = BranchMembership
        fields = [
            # IDs
            'id', 'user', 'branch',
            # User info
            'phone_number', 'first_name', 'last_name', 'email', 'full_name',
            # Role
            'role', 'role_display', 'role_ref', 'role_ref_id', 'role_ref_name', 'title',
            # Financial
            'balance', 'balance_status', 'salary', 'salary_type',
            'monthly_salary', 'hourly_rate', 'per_lesson_rate',
            # Employment
            'hire_date', 'termination_date', 'employment_type', 'employment_type_display',
            'days_employed', 'years_employed', 'is_active_employment',
            # Personal info
            'passport_serial', 'passport_number', 'address', 'emergency_contact',
            # Additional
            'notes',
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class StaffCreateSerializer(serializers.Serializer):
    """Serializer for creating new staff members.
    
    Creates both User and BranchMembership in a single transaction.
    """
    
    # User fields
    phone_number = serializers.CharField(max_length=20, help_text="+998901234567")
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, help_text="Agar bo'sh bo'lsa, avtomatik generatsiya qilinadi")
    
    # Membership fields
    branch_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=BranchRole.choices)
    role_ref_id = serializers.UUIDField(required=False, allow_null=True, help_text="Faqat role='other' uchun")
    title = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Financial fields
    monthly_salary = serializers.IntegerField(default=0, min_value=0)
    hourly_rate = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    per_lesson_rate = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    salary_type = serializers.CharField(default='monthly')
    
    # Employment fields
    hire_date = serializers.DateField(required=False, allow_null=True)
    employment_type = serializers.ChoiceField(
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
        required=False
    )
    
    # Personal info
    passport_serial = serializers.CharField(max_length=2, required=False, allow_blank=True)
    passport_number = serializers.CharField(max_length=7, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    emergency_contact = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_phone_number(self, value):
        """Normalize and validate phone number."""
        # Remove spaces and dashes
        value = value.replace(' ', '').replace('-', '')
        
        # Ensure it starts with +
        if not value.startswith('+'):
            value = '+' + value
        
        # Check if user already exists
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro'yxatdan o'tgan.")
        
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        role = attrs.get('role')
        role_ref_id = attrs.get('role_ref_id')
        
        # If role is 'other', role_ref_id is required
        if role == BranchRole.OTHER and not role_ref_id:
            raise serializers.ValidationError({
                'role_ref_id': "role='other' uchun role_ref_id majburiy"
            })
        
        # Validate role_ref exists if provided
        if role_ref_id:
            if not Role.objects.filter(id=role_ref_id).exists():
                raise serializers.ValidationError({
                    'role_ref_id': "Bunday rol topilmadi"
                })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Create user and membership in a single transaction."""
        # Extract user fields
        phone_number = validated_data['phone_number']
        first_name = validated_data['first_name']
        last_name = validated_data['last_name']
        email = validated_data.get('email', '')
        password = validated_data.get('password')
        
        # Create user
        user = User.objects.create_user(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password if password else User.objects.make_random_password()
        )
        
        # Create membership
        membership = BranchMembership.objects.create(
            user=user,
            branch_id=validated_data['branch_id'],
            role=validated_data['role'],
            role_ref_id=validated_data.get('role_ref_id'),
            title=validated_data.get('title', ''),
            monthly_salary=validated_data.get('monthly_salary', 0),
            hourly_rate=validated_data.get('hourly_rate'),
            per_lesson_rate=validated_data.get('per_lesson_rate'),
            salary_type=validated_data.get('salary_type', 'monthly'),
            hire_date=validated_data.get('hire_date'),
            employment_type=validated_data.get('employment_type', EmploymentType.FULL_TIME),
            passport_serial=validated_data.get('passport_serial', ''),
            passport_number=validated_data.get('passport_number', ''),
            address=validated_data.get('address', ''),
            emergency_contact=validated_data.get('emergency_contact', ''),
        )
        
        return membership


class StaffUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating staff member information."""
    
    # User fields (optional for update)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True)
    
    class Meta:
        model = BranchMembership
        fields = [
            # User info
            'first_name', 'last_name', 'email',
            # Role
            'role', 'role_ref', 'title',
            # Financial
            'monthly_salary', 'hourly_rate', 'per_lesson_rate', 'salary_type',
            # Employment
            'hire_date', 'termination_date', 'employment_type',
            # Personal
            'passport_serial', 'passport_number', 'address', 'emergency_contact',
            # Additional
            'notes',
        ]
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update both user and membership."""
        # Update user fields if provided
        user_data = {}
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()
        
        # Update membership fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class BalanceTransactionSerializer(serializers.ModelSerializer):
    """Serializer for balance transactions."""
    
    staff_name = serializers.CharField(source='membership.user.get_full_name', read_only=True)
    staff_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = BalanceTransaction
        fields = [
            'id', 'membership_id', 'staff_name', 'staff_phone',
            'transaction_type', 'transaction_type_display',
            'amount', 'previous_balance', 'new_balance',
            'reference', 'description',
            'salary_payment_id', 'processed_by', 'processed_by_name',
            'created_at'
        ]
        read_only_fields = ['id', 'previous_balance', 'new_balance', 'created_at']


class SalaryPaymentSerializer(serializers.ModelSerializer):
    """Serializer for salary payments."""
    
    staff_name = serializers.CharField(source='membership.user.get_full_name', read_only=True)
    staff_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'membership_id', 'staff_name', 'staff_phone',
            'month', 'amount', 'payment_date',
            'payment_method', 'payment_method_display',
            'status', 'status_display',
            'notes', 'reference_number',
            'processed_by', 'processed_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaffStatsSerializer(serializers.Serializer):
    """Serializer for staff statistics."""
    
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    terminated = serializers.IntegerField()
    by_role = serializers.DictField()
    by_employment_type = serializers.DictField()
    total_balance = serializers.IntegerField()
    total_salary = serializers.IntegerField()

from rest_framework import serializers

from .models import Branch, Role, BranchMembership, SalaryType


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "status", "type"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "branch",
            "branch_name",
            "permissions",
            "description",
            "is_active",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_members_count(self, obj):
        """Nechta xodim bu roldan foydalanmoqda."""
        return obj.role_memberships.filter(deleted_at__isnull=True).count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new role."""
    
    class Meta:
        model = Role
        fields = [
            "name",
            "branch",
            "permissions",
            "description",
            "is_active",
        ]


class BranchMembershipDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for BranchMembership (admin use)."""
    
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    role_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    effective_role = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()
    salary_display = serializers.CharField(source='get_salary_display', read_only=True)
    
    class Meta:
        model = BranchMembership
        fields = [
            "id",
            "user",
            "user_phone",
            "user_name",
            "branch",
            "branch_name",
            "role",
            "role_ref",
            "role_name",
            "effective_role",
            "title",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_lesson_rate",
            "balance",
            "salary",
            "salary_display",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
    
    def get_user_name(self, obj):
        """Get user full name."""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.phone_number
    
    def get_effective_role(self, obj):
        """Get effective role name."""
        return obj.get_effective_role()
    
    def get_salary(self, obj):
        """Get current salary based on salary_type."""
        return obj.get_salary()
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', self.instance.salary_type if self.instance else SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary', self.instance.monthly_salary if self.instance else 0):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate', self.instance.hourly_rate if self.instance else 0):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_LESSON:
            if not data.get('per_lesson_rate', self.instance.per_lesson_rate if self.instance else 0):
                raise serializers.ValidationError({
                    "per_lesson_rate": "Dars uchun stavka belgilanishi kerak."
                })
        
        return data


class BranchMembershipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new membership (SuperAdmin only)."""
    
    class Meta:
        model = BranchMembership
        fields = [
            "user",
            "role",
            "role_ref",
            "title",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_lesson_rate",
        ]
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary', 0):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate', 0):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_LESSON:
            if not data.get('per_lesson_rate', 0):
                raise serializers.ValidationError({
                    "per_lesson_rate": "Dars uchun stavka belgilanishi kerak."
                })
        
        # Validate user exists
        user = data.get('user')
        if user:
            from auth.users.models import User
            if not User.objects.filter(id=user.id).exists():
                raise serializers.ValidationError({
                    "user": "Foydalanuvchi topilmadi."
                })
        
        return data


class BalanceUpdateSerializer(serializers.Serializer):
    """Serializer for updating membership balance."""
    
    amount = serializers.IntegerField(
        help_text="Qo'shish uchun musbat, ayirish uchun manfiy qiymat (so'm, butun son)"
    )
    note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Balans o'zgarishi sababi"
    )

from rest_framework import serializers

from .models import Branch, Role, BranchMembership, SalaryType


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "status", "type"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "branch",
            "branch_name",
            "permissions",
            "description",
            "is_active",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_members_count(self, obj):
        """Nechta xodim bu roldan foydalanmoqda."""
        return obj.role_memberships.filter(deleted_at__isnull=True).count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new role."""
    
    class Meta:
        model = Role
        fields = [
            "name",
            "branch",
            "permissions",
            "description",
            "is_active",
        ]


class BranchMembershipDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for BranchMembership (admin use)."""
    
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    role_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    effective_role = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()
    salary_display = serializers.CharField(source='get_salary_display', read_only=True)
    
    class Meta:
        model = BranchMembership
        fields = [
            "id",
            "user",
            "user_phone",
            "user_name",
            "branch",
            "branch_name",
            "role",
            "role_ref",
            "role_name",
            "effective_role",
            "title",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_lesson_rate",
            "balance",
            "salary",
            "salary_display",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
    
    def get_user_name(self, obj):
        """Get user full name."""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.phone_number
    
    def get_effective_role(self, obj):
        """Get effective role name."""
        return obj.get_effective_role()
    
    def get_salary(self, obj):
        """Get current salary based on salary_type."""
        return obj.get_salary()
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', self.instance.salary_type if self.instance else SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary', self.instance.monthly_salary if self.instance else 0):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate', self.instance.hourly_rate if self.instance else 0):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_LESSON:
            if not data.get('per_lesson_rate', self.instance.per_lesson_rate if self.instance else 0):
                raise serializers.ValidationError({
                    "per_lesson_rate": "Dars uchun stavka belgilanishi kerak."
                })
        
        return data


class BranchMembershipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new membership (SuperAdmin only)."""
    
    class Meta:
        model = BranchMembership
        fields = [
            "user",
            "role",
            "role_ref",
            "title",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_lesson_rate",
        ]
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary', 0):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate', 0):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_LESSON:
            if not data.get('per_lesson_rate', 0):
                raise serializers.ValidationError({
                    "per_lesson_rate": "Dars uchun stavka belgilanishi kerak."
                })
        
        # Validate user exists
        user = data.get('user')
        if user:
            from auth.users.models import User
            if not User.objects.filter(id=user.id).exists():
                raise serializers.ValidationError({
                    "user": "Foydalanuvchi topilmadi."
                })
        
        return data


class BalanceUpdateSerializer(serializers.Serializer):
    """Serializer for updating membership balance."""
    
    amount = serializers.IntegerField(
        help_text="Qo'shish uchun musbat, ayirish uchun manfiy qiymat (so'm, butun son)"
    )
    note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Balans o'zgarishi sababi"
    )



# Legacy serializers for backward compatibility


from rest_framework import serializers

from .models import Branch, Role, BranchMembership, SalaryType


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "status", "type"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)
    members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "branch",
            "branch_name",
            "permissions",
            "description",
            "is_active",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_members_count(self, obj):
        """Nechta xodim bu roldan foydalanmoqda."""
        return obj.role_memberships.filter(deleted_at__isnull=True).count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new role."""
    
    class Meta:
        model = Role
        fields = [
            "name",
            "branch",
            "permissions",
            "description",
            "is_active",
        ]


class BranchMembershipDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for BranchMembership (admin use)."""
    
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    role_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    effective_role = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()
    salary_display = serializers.CharField(source='get_salary_display', read_only=True)
    
    class Meta:
        model = BranchMembership
        fields = [
            "id",
            "user",
            "user_phone",
            "user_name",
            "branch",
            "branch_name",
            "role",
            "role_ref",
            "role_name",
            "effective_role",
            "title",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_lesson_rate",
            "balance",
            "salary",
            "salary_display",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
    
    def get_user_name(self, obj):
        """Get user full name."""
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return obj.user.phone_number
    
    def get_effective_role(self, obj):
        """Get effective role name."""
        return obj.get_effective_role()
    
    def get_salary(self, obj):
        """Get current salary based on salary_type."""
        return obj.get_salary()
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', self.instance.salary_type if self.instance else SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary', self.instance.monthly_salary if self.instance else 0):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate', self.instance.hourly_rate if self.instance else 0):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_LESSON:
            if not data.get('per_lesson_rate', self.instance.per_lesson_rate if self.instance else 0):
                raise serializers.ValidationError({
                    "per_lesson_rate": "Dars uchun stavka belgilanishi kerak."
                })
        
        return data


class BranchMembershipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new membership (SuperAdmin only)."""
    
    class Meta:
        model = BranchMembership
        fields = [
            "user",
            "role",
            "role_ref",
            "title",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_lesson_rate",
        ]
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary', 0):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate', 0):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_LESSON:
            if not data.get('per_lesson_rate', 0):
                raise serializers.ValidationError({
                    "per_lesson_rate": "Dars uchun stavka belgilanishi kerak."
                })
        
        # Validate user exists
        user = data.get('user')
        if user:
            from auth.users.models import User
            if not User.objects.filter(id=user.id).exists():
                raise serializers.ValidationError({
                    "user": "Foydalanuvchi topilmadi."
                })
        
        return data


class BalanceUpdateSerializer(serializers.Serializer):
    """Serializer for updating membership balance."""
    
    amount = serializers.IntegerField(
        help_text="Qo'shish uchun musbat, ayirish uchun manfiy qiymat (so'm, butun son)"
    )
    note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Balans o'zgarishi sababi"
    )

