"""
Moliya tizimi serializers.
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    CashRegister,
    Transaction,
    StudentBalance,
    SubscriptionPlan,
    Discount,
    Payment,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    SubscriptionPeriod,
    DiscountType,
)
from apps.branch.models import Branch
from auth.profiles.models import StudentProfile


class CashRegisterSerializer(serializers.ModelSerializer):
    """Kassa serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = CashRegister
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'description',
            'balance',
            'is_active',
            'location',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'balance']


class TransactionSerializer(serializers.ModelSerializer):
    """Tranzaksiya serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    cash_register_name = serializers.CharField(source='cash_register.name', read_only=True)
    student_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'branch',
            'branch_name',
            'cash_register',
            'cash_register_name',
            'transaction_type',
            'transaction_type_display',
            'status',
            'status_display',
            'amount',
            'payment_method',
            'payment_method_display',
            'description',
            'reference_number',
            'student_profile',
            'student_name',
            'employee_membership',
            'employee_name',
            'transaction_date',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        """O'quvchi nomini olish."""
        if obj.student_profile:
            return str(obj.student_profile)
        return None
    
    def get_employee_name(self, obj):
        """Xodim nomini olish."""
        if obj.employee_membership:
            return str(obj.employee_membership.user)
        return None


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Tranzaksiya yaratish serializer."""
    
    class Meta:
        model = Transaction
        fields = [
            'branch',
            'cash_register',
            'transaction_type',
            'amount',
            'payment_method',
            'description',
            'reference_number',
            'student_profile',
            'employee_membership',
            'transaction_date',
            'metadata',
        ]
    
    def validate(self, attrs):
        """Validatsiya."""
        amount = attrs.get('amount')
        if amount and amount < 1:
            raise serializers.ValidationError({"amount": "Summa 1 dan katta yoki teng bo'lishi kerak"})
        
        return attrs
    
    def create(self, validated_data):
        """Tranzaksiya yaratish."""
        # Statusni PENDING qilib qo'yamiz
        validated_data['status'] = TransactionStatus.PENDING
        
        # Agar transaction_date ko'rsatilmagan bo'lsa, hozirgi vaqtni qo'yamiz
        if 'transaction_date' not in validated_data:
            validated_data['transaction_date'] = timezone.now()
        
        transaction = super().create(validated_data)
        
        # Agar status COMPLETED bo'lsa, kassa balansini yangilash
        if transaction.status == TransactionStatus.COMPLETED:
            transaction.cash_register.update_balance(transaction.amount, transaction.transaction_type)
        
        return transaction


class StudentBalanceSerializer(serializers.ModelSerializer):
    """O'quvchi balansi serializer."""
    
    student_name = serializers.SerializerMethodField()
    student_personal_number = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentBalance
        fields = [
            'id',
            'student_profile',
            'student_name',
            'student_personal_number',
            'balance',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'balance']
    
    def get_student_name(self, obj):
        """O'quvchi nomini olish."""
        return str(obj.student_profile)
    
    def get_student_personal_number(self, obj):
        """O'quvchi shaxsiy raqamini olish."""
        return obj.student_profile.personal_number


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Abonement tarifi serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    grade_level_range = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'description',
            'grade_level_min',
            'grade_level_max',
            'grade_level_range',
            'period',
            'period_display',
            'price',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_grade_level_range(self, obj):
        """Sinf darajasi diapazonini olish."""
        return f"{obj.grade_level_min}-{obj.grade_level_max}"
    
    def validate(self, attrs):
        """Validatsiya."""
        grade_level_min = attrs.get('grade_level_min')
        grade_level_max = attrs.get('grade_level_max')
        
        if grade_level_min and grade_level_max:
            if grade_level_min > grade_level_max:
                raise serializers.ValidationError({
                    "grade_level_min": "Minimal sinf darajasi maksimaldan katta bo'lishi mumkin emas"
                })
        
        return attrs


class DiscountSerializer(serializers.ModelSerializer):
    """Chegirma serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    is_valid = serializers.SerializerMethodField()
    discount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Discount
        fields = [
            'id',
            'branch',
            'branch_name',
            'name',
            'discount_type',
            'discount_type_display',
            'amount',
            'discount_display',
            'is_active',
            'valid_from',
            'valid_until',
            'description',
            'conditions',
            'is_valid',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_valid']
    
    def get_is_valid(self, obj):
        """Chegirma hozir amal qiladimi?"""
        return obj.is_valid()
    
    def get_discount_display(self, obj):
        """Chegirma ko'rinishini olish."""
        if obj.discount_type == DiscountType.PERCENTAGE:
            return f"{obj.amount}%"
        return f"{obj.amount} so'm"
    
    def validate(self, attrs):
        """Validatsiya."""
        discount_type = attrs.get('discount_type', self.instance.discount_type if self.instance else None)
        amount = attrs.get('amount')
        
        if discount_type == DiscountType.PERCENTAGE and amount:
            if amount > 100:
                raise serializers.ValidationError({
                    "amount": "Foiz 100 dan katta bo'lishi mumkin emas"
                })
        
        valid_from = attrs.get('valid_from')
        valid_until = attrs.get('valid_until')
        
        if valid_from and valid_until:
            if valid_from > valid_until:
                raise serializers.ValidationError({
                    "valid_until": "Tugash sanasi boshlanish sanasidan keyin bo'lishi kerak"
                })
        
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """To'lov serializer."""
    
    student_name = serializers.SerializerMethodField()
    student_personal_number = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    subscription_plan_name = serializers.SerializerMethodField()
    discount_name = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'student_profile',
            'student_name',
            'student_personal_number',
            'branch',
            'branch_name',
            'subscription_plan',
            'subscription_plan_name',
            'base_amount',
            'discount_amount',
            'final_amount',
            'discount',
            'discount_name',
            'payment_method',
            'payment_method_display',
            'period',
            'period_display',
            'payment_date',
            'period_start',
            'period_end',
            'transaction',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student_name(self, obj):
        """O'quvchi nomini olish."""
        return str(obj.student_profile)
    
    def get_student_personal_number(self, obj):
        """O'quvchi shaxsiy raqamini olish."""
        return obj.student_profile.personal_number
    
    def get_subscription_plan_name(self, obj):
        """Abonement tarifi nomini olish."""
        if obj.subscription_plan:
            return str(obj.subscription_plan)
        return None
    
    def get_discount_name(self, obj):
        """Chegirma nomini olish."""
        if obj.discount:
            return str(obj.discount)
        return None


class PaymentCreateSerializer(serializers.ModelSerializer):
    """To'lov yaratish serializer."""
    
    cash_register = serializers.UUIDField(
        write_only=True,
        required=True,
        help_text='Kassa ID (Transaction yaratish uchun)'
    )
    
    class Meta:
        model = Payment
        fields = [
            'student_profile',
            'branch',
            'subscription_plan',
            'base_amount',
            'discount',
            'payment_method',
            'period',
            'payment_date',
            'period_start',
            'period_end',
            'cash_register',
            'notes',
        ]
    
    def validate(self, attrs):
        """Validatsiya."""
        student_profile = attrs.get('student_profile')
        branch = attrs.get('branch')
        subscription_plan = attrs.get('subscription_plan')
        base_amount = attrs.get('base_amount')
        discount = attrs.get('discount')
        cash_register_id = attrs.get('cash_register')
        
        # Filial tekshiruvi
        if student_profile and branch:
            if student_profile.user_branch.branch != branch:
                raise serializers.ValidationError({
                    "student_profile": "O'quvchi bu filialga tegishli emas"
                })
        
        # Kassa tekshiruvi
        if cash_register_id and branch:
            from .models import CashRegister
            try:
                cash_register = CashRegister.objects.get(
                    id=cash_register_id,
                    branch=branch,
                    deleted_at__isnull=True
                )
                attrs['cash_register'] = cash_register
            except CashRegister.DoesNotExist:
                raise serializers.ValidationError({
                    "cash_register": "Kassa topilmadi yoki bu filialga tegishli emas"
                })
        
        # Abonement tarifi tekshiruvi (umumiy tariflar ham qo'llanadi)
        if subscription_plan and branch:
            if subscription_plan.branch and subscription_plan.branch != branch:
                raise serializers.ValidationError({
                    "subscription_plan": "Abonement tarifi bu filialga tegishli emas"
                })
        
        # Chegirma tekshiruvi (umumiy chegirmalar ham qo'llanadi)
        if discount and branch:
            if discount.branch and discount.branch != branch:
                raise serializers.ValidationError({
                    "discount": "Chegirma bu filialga tegishli emas"
                })
        
        # Chegirmani hisoblash
        discount_amount = 0
        if discount and discount.is_valid():
            discount_amount = discount.calculate_discount(base_amount)
        
        # Final amount
        final_amount = base_amount - discount_amount
        if final_amount <= 0:
            raise serializers.ValidationError({
                "base_amount": "Chegirma asosiy summani oshib ketdi"
            })
        
        attrs['discount_amount'] = discount_amount
        attrs['final_amount'] = final_amount
        
        return attrs
    
    def create(self, validated_data):
        """To'lov yaratish."""
        cash_register = validated_data.pop('cash_register')
        student_profile = validated_data.get('student_profile')
        branch = validated_data.get('branch')
        final_amount = validated_data.get('final_amount')
        
        # Tranzaksiya yaratish
        transaction = Transaction.objects.create(
            branch=branch,
            cash_register=cash_register,
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.COMPLETED,
            amount=final_amount,
            payment_method=validated_data.get('payment_method', PaymentMethod.CASH),
            description=f"O'quvchi to'lovi: {student_profile}",
            student_profile=student_profile,
            transaction_date=validated_data.get('payment_date', timezone.now()),
        )
        
        # To'lov yaratish
        validated_data['transaction'] = transaction
        payment = super().create(validated_data)
        
        # O'quvchi balansini yangilash
        student_balance, _ = StudentBalance.objects.get_or_create(
            student_profile=student_profile
        )
        student_balance.add_amount(final_amount)
        
        return payment

