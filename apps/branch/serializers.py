from __future__ import annotations


from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db import models
from apps.branch.models import (
    BranchMembership, BalanceTransaction, SalaryPayment,
    Role, BranchRole, EmploymentType, BranchSettings
)
from apps.branch.choices import TransactionType, PaymentMethod, PaymentStatus

User = get_user_model()


class StaffListSerializer(serializers.ModelSerializer):
    """Compact serializer for staff listing.
    
    Returns only essential information for list views.
    """
    
    # User information
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Role information
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    role_ref_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    
    # Computed fields
    is_active = serializers.SerializerMethodField()
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    
    def get_is_active(self, obj):
        """Check if staff member is currently active."""
        return obj.termination_date is None
    
    class Meta:
        model = BranchMembership
        fields = [
            'id',
            'full_name',
            'phone_number',
            'role',
            'role_display',
            'role_ref_name',
            'title',
            'employment_type',
            'employment_type_display',
            'hire_date',
            'balance',
            'monthly_salary',
            'is_active',
        ]


class StaffDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for staff member with all related data.
    
    Includes transactions, payments, and complete profile information.
    """
    
    # User information
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True, allow_null=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    # Branch information
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    branch_type = serializers.CharField(source='branch.type', read_only=True)
    
    # Role information
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    role_ref_id = serializers.UUIDField(source='role_ref.id', read_only=True, allow_null=True)
    role_ref_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    role_ref_permissions = serializers.JSONField(source='role_ref.permissions', read_only=True, allow_null=True)
    
    # Computed fields
    salary = serializers.IntegerField(source='get_salary', read_only=True)
    days_employed = serializers.IntegerField(read_only=True)
    years_employed = serializers.FloatField(read_only=True)
    is_active_employment = serializers.BooleanField(read_only=True)
    balance_status = serializers.CharField(read_only=True)
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    
    # Related data
    recent_transactions = serializers.SerializerMethodField()
    recent_payments = serializers.SerializerMethodField()
    transaction_summary = serializers.SerializerMethodField()
    payment_summary = serializers.SerializerMethodField()
    
    def get_recent_transactions(self, obj):
        """Get last 10 transactions."""
        transactions = obj.balance_transactions.select_related('processed_by').order_by('-created_at')[:10]
        return BalanceTransactionSerializer(transactions, many=True).data
    
    def get_recent_payments(self, obj):
        """Get last 10 salary payments."""
        payments = obj.salary_payments.select_related('processed_by').order_by('-payment_date')[:10]
        return SalaryPaymentSerializer(payments, many=True).data
    
    def get_transaction_summary(self, obj):
        """Summary of all transactions."""
        from django.db.models import Sum, Count
        from apps.branch.choices import TransactionType
        
        summary = obj.balance_transactions.aggregate(
            total_count=Count('id'),
            total_debit=Sum('amount', filter=models.Q(transaction_type__in=[
                TransactionType.SALARY_ACCRUAL, TransactionType.BONUS
            ])),
            total_credit=Sum('amount', filter=models.Q(transaction_type__in=[
                TransactionType.DEDUCTION, TransactionType.ADVANCE, TransactionType.FINE
            ])),
        )
        
        return {
            'total_transactions': summary['total_count'] or 0,
            'total_received': summary['total_debit'] or 0,
            'total_deducted': summary['total_credit'] or 0,
        }
    
    def get_payment_summary(self, obj):
        """Summary of salary payments."""
        from django.db.models import Sum, Count
        from apps.branch.choices import PaymentStatus
        
        payments = obj.salary_payments.aggregate(
            total_count=Count('id'),
            total_paid=Sum('amount', filter=models.Q(status=PaymentStatus.PAID)),
            pending_count=Count('id', filter=models.Q(status=PaymentStatus.PENDING)),
        )
        
        return {
            'total_payments': payments['total_count'] or 0,
            'total_amount_paid': payments['total_paid'] or 0,
            'pending_payments': payments['pending_count'] or 0,
        }
    
    class Meta:
        model = BranchMembership
        fields = [
            # IDs
            'id', 'user_id', 'branch', 'branch_name', 'branch_type',
            # User info
            'phone_number', 'first_name', 'last_name', 'email', 'full_name',
            # Role
            'role', 'role_display', 'role_ref', 'role_ref_id', 'role_ref_name', 
            'role_ref_permissions', 'title',
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
            # Related data
            'recent_transactions', 'recent_payments',
            'transaction_summary', 'payment_summary',
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at']


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
    balance_change = serializers.SerializerMethodField()
    
    class Meta:
        model = BalanceTransaction
        fields = [
            'id', 'membership', 'staff_name', 'staff_phone',
            'transaction_type', 'transaction_type_display',
            'amount', 'previous_balance', 'new_balance', 'balance_change',
            'reference', 'description',
            'salary_payment', 'processed_by', 'processed_by_name',
            'created_at'
        ]
        read_only_fields = ['id', 'membership', 'previous_balance', 'new_balance', 'balance_change', 'created_at']
    
    def get_balance_change(self, obj):
        """Calculate balance change (positive or negative)."""
        return obj.new_balance - obj.previous_balance
    
    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class SalaryPaymentSerializer(serializers.ModelSerializer):
    """Serializer for salary payments."""
    
    staff_name = serializers.CharField(source='membership.user.get_full_name', read_only=True)
    staff_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True, allow_null=True)
    month_display = serializers.SerializerMethodField()
    
    class Meta:
        model = SalaryPayment
        fields = [
            'id', 'membership', 'staff_name', 'staff_phone',
            'month', 'month_display', 'amount', 'payment_date',
            'payment_method', 'payment_method_display',
            'payment_type', 'payment_type_display',
            'status', 'status_display',
            'notes', 'reference_number',
            'processed_by', 'processed_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'membership', 'created_at', 'updated_at']
    
    def get_month_display(self, obj):
        """Format month as readable string."""
        return obj.month.strftime('%B %Y')  # e.g., "December 2024"
    
    def validate_amount(self, value):
        """Validate amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def validate_month(self, value):
        """Validate month is not in future."""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Cannot pay salary for future months")
        return value


class SalaryCalculationSerializer(serializers.Serializer):
    """Serializer for salary calculation responses."""
    
    success = serializers.BooleanField()
    monthly_salary = serializers.IntegerField(required=False)
    days_in_month = serializers.IntegerField(required=False)
    daily_salary = serializers.IntegerField(required=False)
    total_amount = serializers.IntegerField(required=False)
    days_worked = serializers.IntegerField(required=False)
    prorated_amount = serializers.IntegerField(required=False)
    year = serializers.IntegerField(required=False)
    month = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    reason = serializers.CharField(required=False)


class SalaryAccrualRequestSerializer(serializers.Serializer):
    """Request serializer for adding salary accrual."""
    
    amount = serializers.IntegerField(min_value=1, help_text="Accrual amount in som")
    description = serializers.CharField(help_text="Description of the accrual")
    reference = serializers.CharField(required=False, allow_blank=True, help_text="Reference number")


class BalanceChangeRequestSerializer(serializers.Serializer):
    """Request serializer for changing staff balance with optional cash transaction."""
    
    transaction_type = serializers.ChoiceField(
        choices=TransactionType.choices,
        help_text="Type of balance transaction"
    )
    amount = serializers.IntegerField(min_value=1, help_text="Amount in som")
    description = serializers.CharField(help_text="Description of the transaction")
    
    # Optional fields for cash transaction
    create_cash_transaction = serializers.BooleanField(
        default=False,
        help_text="Whether to create cash register transaction (for payments)"
    )
    cash_register_id = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Cash register ID (required if create_cash_transaction=true)"
    )
    payment_method = serializers.ChoiceField(
        choices=PaymentMethod.choices,
        default='cash',
        help_text="Payment method for cash transaction"
    )
    reference = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Reference number"
    )
    
    def validate_cash_register_id(self, value):
        """Validate and convert cash_register_id to UUID."""
        if not value:
            return None
        
        import uuid
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            raise serializers.ValidationError("Must be a valid UUID.")
    
    def validate(self, data):
        """Validate cash transaction settings based on transaction type."""
        transaction_type = data.get('transaction_type')
        create_cash_transaction = data.get('create_cash_transaction', False)
        cash_register_id = data.get('cash_register_id')
        
        # Check if cash_register_id is provided when needed
        if create_cash_transaction and not cash_register_id:
            raise serializers.ValidationError({
                'cash_register_id': 'Cash register ID is required when create_cash_transaction is True'
            })
        
        # Prevent cash transaction for balance accrual types
        if create_cash_transaction and transaction_type in [
            TransactionType.SALARY_ACCRUAL,
            TransactionType.BONUS,
            TransactionType.OTHER
        ]:
            raise serializers.ValidationError({
                'create_cash_transaction': f'Cannot create cash transaction for {transaction_type}. '
                                          'Cash transactions are only for payments (deduction, advance, fine, adjustment).'
            })
        
        return data


class SalaryPaymentRequestSerializer(serializers.Serializer):
    """Request serializer for processing salary payment."""
    
    amount = serializers.IntegerField(min_value=1, help_text="Payment amount in som")
    payment_date = serializers.DateField(help_text="Date of payment")
    payment_method = serializers.ChoiceField(
        choices=PaymentMethod.choices,
        help_text="Payment method"
    )
    month = serializers.DateField(help_text="Month for which salary is paid (YYYY-MM-01)")
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Additional notes")
    reference_number = serializers.CharField(required=False, allow_blank=True, help_text="Payment reference")
    
    def validate_month(self, value):
        """Ensure month is first day of month."""
        if value.day != 1:
            raise serializers.ValidationError("Month must be the first day (YYYY-MM-01)")
        return value
    
    def validate_payment_date(self, value):
        """Validate payment date is not in future."""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Payment date cannot be in the future")
        return value


class MonthlySalarySummarySerializer(serializers.Serializer):
	"""Serializer for monthly salary summary."""
	
	year = serializers.IntegerField()
	month = serializers.IntegerField()
	total_accrued = serializers.IntegerField()
	total_paid = serializers.IntegerField()
	balance_change = serializers.IntegerField()
	payments_count = serializers.IntegerField()
	transactions_count = serializers.IntegerField()


class BalanceTransactionListSerializer(serializers.ModelSerializer):
	"""Serializer for balance transaction list view."""
	
	# Staff information
	staff_id = serializers.UUIDField(source='membership.id', read_only=True)
	staff_name = serializers.CharField(source='membership.user.get_full_name', read_only=True)
	staff_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
	staff_role = serializers.CharField(source='membership.get_role_display', read_only=True)
	
	# Transaction type display
	transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
	
	# Balance changes
	balance_change = serializers.SerializerMethodField()
	
	# Processed by
	processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
	processed_by_phone = serializers.CharField(source='processed_by.phone_number', read_only=True)
	
	# Salary payment info (if linked)
	salary_payment_id = serializers.UUIDField(source='salary_payment.id', read_only=True, allow_null=True)
	salary_payment_month = serializers.DateField(source='salary_payment.month', read_only=True, allow_null=True)
	
	def get_balance_change(self, obj):
		"""Calculate balance change (negative for deductions)."""
		return obj.new_balance - obj.previous_balance
	
	class Meta:
		model = BalanceTransaction
		fields = [
			'id',
			'staff_id',
			'staff_name',
			'staff_phone',
			'staff_role',
			'transaction_type',
			'transaction_type_display',
			'amount',
			'previous_balance',
			'new_balance',
			'balance_change',
			'reference',
			'description',
			'salary_payment_id',
			'salary_payment_month',
			'processed_by_name',
			'processed_by_phone',
			'created_at',
			'updated_at',
		]
		read_only_fields = fields


class SalaryPaymentListSerializer(serializers.ModelSerializer):
	"""Serializer for salary payment list view."""
	
	# Staff information
	staff_id = serializers.UUIDField(source='membership.id', read_only=True)
	staff_name = serializers.CharField(source='membership.user.get_full_name', read_only=True)
	staff_phone = serializers.CharField(source='membership.user.phone_number', read_only=True)
	staff_role = serializers.CharField(source='membership.get_role_display', read_only=True)
	staff_monthly_salary = serializers.IntegerField(source='membership.monthly_salary', read_only=True)
	
	# Display values
	month_display = serializers.SerializerMethodField()
	payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
	payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
	status_display = serializers.CharField(source='get_status_display', read_only=True)
	
	# Processed by
	processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
	processed_by_phone = serializers.CharField(source='processed_by.phone_number', read_only=True)
	
	# Related transactions count
	transactions_count = serializers.SerializerMethodField()
	
	def get_month_display(self, obj):
		"""Return formatted month (e.g., 'January 2024')."""
		return obj.month.strftime('%B %Y')
	
	def get_transactions_count(self, obj):
		"""Count related transactions."""
		return obj.transactions.count()
	
	class Meta:
		model = SalaryPayment
		fields = [
			'id',
			'staff_id',
			'staff_name',
			'staff_phone',
			'staff_role',
			'staff_monthly_salary',
			'month',
			'month_display',
			'amount',
			'payment_date',
			'payment_method',
			'payment_method_display',
			'payment_type',
			'payment_type_display',
			'status',
			'status_display',
			'status',
			'status_display',
			'notes',
			'reference_number',
			'transactions_count',
			'processed_by_name',
			'processed_by_phone',
			'created_at',
			'updated_at',
		]
		read_only_fields = fields
class StaffStatsSerializer(serializers.Serializer):
    """Serializer for staff statistics."""
    
    # Xodimlar soni
    total_staff = serializers.IntegerField(help_text="Jami xodimlar soni")
    active_staff = serializers.IntegerField(help_text="Faol xodimlar soni")
    terminated_staff = serializers.IntegerField(help_text="Ishdan bo'shatilgan xodimlar")
    
    # Lavozim bo'yicha
    by_employment_type = serializers.ListField(help_text="Ish turi bo'yicha (to'liq vaqt, yarim vaqt)")
    by_role = serializers.ListField(help_text="Asosiy lavozim bo'yicha (o'qituvchi, admin, etc)")
    by_custom_role = serializers.ListField(help_text="Maxsus lavozimlar bo'yicha")
    
    # Maosh statistikasi
    average_salary = serializers.FloatField(help_text="O'rtacha oylik maosh")
    total_salary_budget = serializers.IntegerField(help_text="Oylik umumiy maosh byudjeti")
    max_salary = serializers.IntegerField(help_text="Eng yuqori maosh")
    min_salary = serializers.IntegerField(help_text="Eng past maosh")
    
    # To'lovlar statistikasi
    total_paid = serializers.IntegerField(help_text="Jami to'langan summa")
    total_pending = serializers.IntegerField(help_text="Kutilayotgan to'lovlar summasi")
    paid_payments_count = serializers.IntegerField(help_text="To'langan to'lovlar soni")
    pending_payments_count = serializers.IntegerField(help_text="Kutilayotgan to'lovlar soni")
    
    # Balans statistikasi
    total_balance = serializers.IntegerField(help_text="Xodimlarning umumiy balansi")


class BranchSettingsSerializer(serializers.ModelSerializer):
    """Filial sozlamalari uchun serializer."""
    
    branch_id = serializers.UUIDField(source='branch.id', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = BranchSettings
        fields = [
            'id',
            'branch_id',
            'branch_name',
            
            # Dars jadvali
            'lesson_duration_minutes',
            'break_duration_minutes',
            'school_start_time',
            'school_end_time',
            
            # Akademik
            'academic_year_start_month',
            'academic_year_end_month',
            
            # Moliya
            'currency',
            'currency_symbol',
            
            # Maosh hisoblash
            'salary_calculation_time',
            'auto_calculate_salary',
            'salary_calculation_day',
            
            # To'lovlar
            'late_payment_penalty_percent',
            'early_payment_discount_percent',
            
            # Ish vaqti
            'work_days_per_week',
            'work_hours_per_day',
            
            # Qo'shimcha
            'additional_settings',
            
            # Meta
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'branch_id', 'branch_name', 'created_at', 'updated_at']
        
    def validate_salary_calculation_day(self, value):
        """Validate salary calculation day."""
        if not 1 <= value <= 31:
            raise serializers.ValidationError("Kun 1 dan 31 gacha bo'lishi kerak")
        return value
    
    def validate_work_days_per_week(self, value):
        """Validate work days per week."""
        if not 1 <= value <= 7:
            raise serializers.ValidationError("Haftalik ish kunlari 1 dan 7 gacha bo'lishi kerak")
        return value


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

