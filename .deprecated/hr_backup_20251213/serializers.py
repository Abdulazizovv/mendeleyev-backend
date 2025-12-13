"""HR API serializers."""

from rest_framework import serializers
from apps.hr.models import StaffRole, StaffProfile, BalanceTransaction, SalaryPayment
from apps.hr.choices import (
    EmploymentType, StaffStatus, TransactionType, 
    PaymentMethod, PaymentStatus
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserCheckSerializer(serializers.Serializer):
    """Serializer for checking user existence."""
    
    phone_number = serializers.CharField(required=True)
    branch_id = serializers.UUIDField(required=False, allow_null=True)


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
    """Enhanced serializer for list views with detailed information."""
    
    # User ma'lumotlari
    user_name = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    # Branch va rol ma'lumotlari
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    role_name = serializers.CharField(source='staff_role.name', read_only=True)
    role_code = serializers.CharField(source='staff_role.code', read_only=True)
    
    # Status display
    employment_type_display = serializers.CharField(
        source='get_employment_type_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    # Qo'shimcha hisoblar
    balance_status = serializers.SerializerMethodField()
    days_employed = serializers.SerializerMethodField()
    is_active_membership = serializers.SerializerMethodField()
    
    class Meta:
        model = StaffProfile
        fields = [
            'id', 'user', 'user_name', 'phone_number', 'email',
            'branch', 'branch_name',
            'staff_role', 'role_name', 'role_code',
            'employment_type', 'employment_type_display',
            'base_salary', 'current_balance', 'balance_status',
            'status', 'status_display',
            'hire_date', 'termination_date', 'days_employed',
            'is_active_membership',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_user_name(self, obj):
        """To'liq ism yoki telefon raqam."""
        return obj.user.get_full_name() or obj.user.phone_number
    
    def get_balance_status(self, obj):
        """Balans holati (positive/negative/zero)."""
        if obj.current_balance > 0:
            return 'positive'
        elif obj.current_balance < 0:
            return 'negative'
        return 'zero'
    
    def get_days_employed(self, obj):
        """Ishlagan kunlar soni."""
        if not obj.hire_date:
            return None
        
        from django.utils import timezone
        end_date = obj.termination_date or timezone.now().date()
        delta = end_date - obj.hire_date
        return delta.days
    
    def get_is_active_membership(self, obj):
        """BranchMembership faolmi."""
        if obj.membership:
            return obj.membership.is_active
        return False


class StaffProfileCreateSerializer(serializers.Serializer):
    """
    Enhanced serializer for creating staff profile.
    Supports atomic creation of User + BranchMembership + StaffProfile.
    """
    
    # User ma'lumotlari (majburiy)
    phone_number = serializers.CharField(
        max_length=20,
        help_text="Telefon raqam (+998901234567 formatida)"
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Agar berilmasa, parolsiz user yaratiladi"
    )
    
    # Staff profile ma'lumotlari (majburiy)
    branch_id = serializers.UUIDField(help_text="Filial ID (UUID)")
    staff_role_id = serializers.UUIDField(help_text="Xodim roli ID (UUID)")
    employment_type = serializers.ChoiceField(
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    hire_date = serializers.DateField(help_text="Ishga qabul qilish sanasi")
    base_salary = serializers.IntegerField(
        min_value=0,
        help_text="Asosiy maosh (UZS)"
    )
    
    # Qo'shimcha ma'lumotlar (ixtiyoriy)
    bank_account = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tax_id = serializers.CharField(max_length=50, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_phone_number(self, value):
        """Telefon raqamni normalizatsiya qilish."""
        # Bo'sh joylarni olib tashlash
        value = value.strip().replace(' ', '').replace('-', '')
        
        # +998 bilan boshlanishini tekshirish
        if not value.startswith('+998'):
            if value.startswith('998'):
                value = '+' + value
            elif value.startswith('8'):
                value = '+99' + value
            else:
                value = '+998' + value
        
        # Uzunlikni tekshirish
        if len(value) != 13:
            raise serializers.ValidationError(
                "Telefon raqam noto'g'ri formatda. To'g'ri format: +998901234567"
            )
        
        return value
    
    def validate_branch_id(self, value):
        """Filial mavjudligini tekshirish."""
        from apps.branch.models import Branch
        
        try:
            branch = Branch.objects.get(pk=value, deleted_at__isnull=True)
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Bunday filial topilmadi.")
        
        return value
    
    def validate_staff_role_id(self, value):
        """Staff role mavjudligini tekshirish."""
        try:
            role = StaffRole.objects.get(pk=value, deleted_at__isnull=True)
            if not role.is_active:
                raise serializers.ValidationError("Bu rol faol emas.")
        except StaffRole.DoesNotExist:
            raise serializers.ValidationError("Bunday xodim roli topilmadi.")
        
        return value
    
    def validate(self, data):
        """Kompleks validatsiya."""
        from apps.branch.models import Branch
        
        # Rol va filial bir xil ekanligini tekshirish
        branch_id = data.get('branch_id')
        role_id = data.get('staff_role_id')
        
        if role_id:
            role = StaffRole.objects.get(pk=role_id)
            if role.branch_id != branch_id:
                raise serializers.ValidationError({
                    'staff_role_id': 'Bu rol boshqa filialga tegishli.'
                })
        
        # Maosh rolning diapazonida ekanligini tekshirish
        base_salary = data.get('base_salary')
        if role_id and base_salary:
            role = StaffRole.objects.get(pk=role_id)
            if role.salary_range_min and base_salary < role.salary_range_min:
                raise serializers.ValidationError({
                    'base_salary': f'Maosh minimal qiymatdan ({role.salary_range_min} UZS) kam bo\'lishi mumkin emas.'
                })
            if role.salary_range_max and base_salary > role.salary_range_max:
                raise serializers.ValidationError({
                    'base_salary': f'Maosh maksimal qiymatdan ({role.salary_range_max} UZS) oshib ketishi mumkin emas.'
                })
        
        # Telefon raqam allaqachon boshqa filialda xodim sifatida mavjudligini tekshirish
        phone_number = data.get('phone_number')
        if phone_number and branch_id:
            user = User.objects.filter(phone_number=phone_number).first()
            if user:
                existing_staff = StaffProfile.objects.filter(
                    user=user,
                    branch_id=branch_id,
                    deleted_at__isnull=True
                ).first()
                if existing_staff:
                    raise serializers.ValidationError({
                        'phone_number': 'Bu foydalanuvchi bu filialda allaqachon xodim sifatida ro\'yxatdan o\'tgan.'
                    })
        
        return data
    
    def create(self, validated_data):
        """Xodim yaratish (User + BranchMembership + StaffProfile)."""
        from apps.branch.models import Branch, BranchMembership
        from django.db import transaction
        
        with transaction.atomic():
            # 1. User yaratish yoki olish
            phone_number = validated_data['phone_number']
            first_name = validated_data['first_name']
            last_name = validated_data.get('last_name', '')
            email = validated_data.get('email', '')
            password = validated_data.get('password')
            
            user, user_created = User.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone_verified': False,
                }
            )
            
            # User allaqachon mavjud bo'lsa, ma'lumotlarni yangilash
            if not user_created:
                if first_name and not user.first_name:
                    user.first_name = first_name
                if last_name and not user.last_name:
                    user.last_name = last_name
                if email and not user.email:
                    user.email = email
                user.save()
            
            # Parol o'rnatish
            if password:
                user.set_password(password)
                user.save()
            elif user_created:
                user.set_unusable_password()
                user.save()
            
            # 2. BranchMembership yaratish yoki olish
            branch_id = validated_data['branch_id']
            branch = Branch.objects.get(pk=branch_id)
            
            membership, membership_created = BranchMembership.objects.get_or_create(
                user=user,
                branch=branch,
                defaults={
                    'role': 'staff',  # Default rol
                }
            )
            
            # Agar soft-deleted bo'lsa, tiklash
            if membership.deleted_at:
                membership.deleted_at = None
                membership.save()
            
            # 3. StaffProfile yaratish
            staff_role = StaffRole.objects.get(pk=validated_data['staff_role_id'])
            
            staff_profile = StaffProfile.objects.create(
                user=user,
                branch=branch,
                membership=membership,
                staff_role=staff_role,
                employment_type=validated_data['employment_type'],
                hire_date=validated_data['hire_date'],
                base_salary=validated_data['base_salary'],
                bank_account=validated_data.get('bank_account', ''),
                tax_id=validated_data.get('tax_id', ''),
                notes=validated_data.get('notes', ''),
                status='active',
                current_balance=0,
                created_by=self.context['request'].user,
            )
            
            return staff_profile


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
