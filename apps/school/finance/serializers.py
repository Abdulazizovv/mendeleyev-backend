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
    StudentSubscription,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    SubscriptionPeriod,
    DiscountType,
    FinanceCategory,
)
from apps.branch.models import Branch
from auth.profiles.models import StudentProfile


class FinanceCategorySerializer(serializers.ModelSerializer):
    """Moliya kategoriyasi serializer."""
    
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False,
        allow_null=True
    )
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    subcategories_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FinanceCategory
        fields = [
            'id',
            'branch',
            'branch_name',
            'type',
            'type_display',
            'name',
            'description',
            'parent',
            'parent_name',
            'subcategories_count',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        # unique_together validation'ni o'chirish - custom validate'da boshqaramiz
        validators = []
    
    def get_subcategories_count(self, obj):
        """Subkategoriyalar soni."""
        return obj.subcategories.filter(is_active=True).count()
    
    def validate(self, attrs):
        """Umumiy validatsiya."""
        branch = attrs.get('branch')
        type_val = attrs.get('type')
        name = attrs.get('name')
        parent = attrs.get('parent')
        
        # Agar parent bo'lsa, bir xil tur bo'lishi kerak
        if parent and parent.type != type_val:
            raise serializers.ValidationError({
                'parent': f"Ota kategoriya {parent.get_type_display()} turida, lekin yangi kategoriya {type_val} turida."
            })
        
        # Unique check (branch, type, name)
        queryset = FinanceCategory.objects.filter(
            branch=branch,
            type=type_val,
            name=name
        )
        
        # Update da o'zini e'tiborsiz qoldirish
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            branch_str = branch.name if branch else "Global"
            raise serializers.ValidationError({
                'name': f"{branch_str} filialda {type_val} turida '{name}' nomli kategoriya mavjud."
            })
        
        return attrs


class FinanceCategoryListSerializer(serializers.ModelSerializer):
    """Kategoriyalar ro'yxati uchun sodda serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = FinanceCategory
        fields = ['id', 'branch', 'branch_name', 'type', 'type_display', 'name', 'is_active']


class CashRegisterSerializer(serializers.ModelSerializer):
    """Kassa serializer."""
    
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False
    )
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
        validators = []  # Custom validation


class TransactionSerializer(serializers.ModelSerializer):
    """Tranzaksiya serializer."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    cash_register_name = serializers.CharField(source='cash_register.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    student = serializers.SerializerMethodField()
    employee = serializers.SerializerMethodField()
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
            'category',
            'category_name',
            'amount',
            'payment_method',
            'payment_method_display',
            'description',
            'reference_number',
            'student_profile',
            'student',
            'employee_membership',
            'employee',
            'transaction_date',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_student(self, obj):
        """O'quvchi to'liq ma'lumotlarini olish."""
        if obj.student_profile:
            student = obj.student_profile
            return {
                'id': str(student.id),
                'personal_number': student.personal_number,
                'full_name': student.full_name,
                'phone_number': student.user_branch.user.phone_number if hasattr(student, 'user_branch') else None,
                'status': student.status,
                'status_display': student.get_status_display(),
                'current_class': {
                    'id': str(student.current_class.id),
                    'name': student.current_class.name,
                } if student.current_class else None,
            }
        return None
    
    def get_employee(self, obj):
        """Xodim to'liq ma'lumotlarini olish."""
        if obj.employee_membership:
            membership = obj.employee_membership
            user = membership.user
            profile = getattr(user, 'profile', None)
            
            employee_data = {
                'id': str(membership.id),
                'user_id': str(user.id),
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'phone_number': user.phone_number,
                'email': user.email,
                'role': membership.role,
                'role_display': membership.get_role_display(),
                'is_active': membership.is_active,
            }
            
            # Avatar qo'shish
            if profile and profile.avatar:
                try:
                    employee_data['avatar'] = profile.avatar.url
                    # To'liq URL
                    request = self.context.get('request')
                    if request:
                        employee_data['avatar_url'] = request.build_absolute_uri(profile.avatar.url)
                    else:
                        employee_data['avatar_url'] = None
                except:
                    employee_data['avatar'] = None
                    employee_data['avatar_url'] = None
            else:
                employee_data['avatar'] = None
                employee_data['avatar_url'] = None
            
            return employee_data
        return None


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Tranzaksiya yaratish serializer."""
    
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False
    )
    auto_approve = serializers.BooleanField(
        default=False,
        write_only=True,
        required=False,
        help_text='Avtomatik tasdiqlash (COMPLETED status)'
    )
    
    class Meta:
        model = Transaction
        fields = [
            'branch',
            'cash_register',
            'transaction_type',
            'category',
            'amount',
            'payment_method',
            'description',
            'reference_number',
            'student_profile',
            'employee_membership',
            'transaction_date',
            'metadata',
            'auto_approve',
        ]
        extra_kwargs = {
            'branch': {'required': False}
        }
        validators = []  # Custom validation
    
    def validate_amount(self, value):
        """Summa validatsiyasi."""
        if value < 1:
            raise serializers.ValidationError("Summa 1 dan katta yoki teng bo'lishi kerak")
        if value > 1_000_000_000:
            raise serializers.ValidationError("Summa 1 milliarddan oshmasligi kerak")
        return value
    
    def validate(self, attrs):
        """Validatsiya."""
        transaction_type = attrs.get('transaction_type')
        cash_register = attrs.get('cash_register')
        amount = attrs.get('amount')
        category = attrs.get('category')
        
        # Kategoriya validatsiyasi
        if category:
            # Kategoriya tipi tranzaksiya tipiga mos kelishi kerak
            if transaction_type == TransactionType.INCOME and category.type != 'income':
                raise serializers.ValidationError({
                    'category': 'Kirim tranzaksiyasi uchun kirim kategoriyasini tanlang'
                })
            if transaction_type == TransactionType.EXPENSE and category.type != 'expense':
                raise serializers.ValidationError({
                    'category': 'Chiqim tranzaksiyasi uchun chiqim kategoriyasini tanlang'
                })
            
            # Kategoriya faol bo'lishi kerak
            if not category.is_active:
                raise serializers.ValidationError({
                    'category': 'Bu kategoriya faol emas'
                })
        
        # Chiqim uchun kassa balansini tekshirish
        if transaction_type in [TransactionType.EXPENSE, TransactionType.SALARY]:
            if cash_register and cash_register.balance < amount:
                raise serializers.ValidationError({
                    'amount': f"Kassada yetarli mablag' yo'q. Mavjud: {cash_register.balance} so'm"
                })
        
        return attrs
    
    def create(self, validated_data):
        """Tranzaksiya yaratish."""
        # Auto-approve flag ni olish va o'chirish (model fieldda yo'q)
        auto_approve = validated_data.pop('auto_approve', False)
        
        # Status aniqlash:
        # - Branch Admin: COMPLETED (avtomatik tasdiq)
        # - Super Admin/Accountant: PENDING (manual tasdiq)
        if auto_approve:
            validated_data['status'] = TransactionStatus.COMPLETED
        else:
            validated_data['status'] = TransactionStatus.PENDING
        
        # Agar transaction_date ko'rsatilmagan bo'lsa, hozirgi vaqtni qo'yamiz
        if 'transaction_date' not in validated_data:
            validated_data['transaction_date'] = timezone.now()
        
        # Transaction yaratish - super().create() Transaction(**validated_data).save() ni chaqiradi
        # Bu Transaction.save() metodini ishga tushiradi va kassa balansini yangilaydi
        transaction = super().create(validated_data)
        
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
    
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False,
        allow_null=True
    )
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
        extra_kwargs = {
            'branch': {'required': False, 'allow_null': True}
        }
        validators = []  # Custom validation
    
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
    
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False,
        allow_null=True
    )
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
        extra_kwargs = {
            'branch': {'required': False, 'allow_null': True}
        }
        validators = []  # Custom validation
    
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
    
    student = serializers.SerializerMethodField()
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
            'student',
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
    
    def get_student(self, obj):
        """O'quvchi to'liq ma'lumotlarini olish."""
        if obj.student_profile:
            student = obj.student_profile
            user = student.user_branch.user if hasattr(student, 'user_branch') else None
            
            student_data = {
                'id': str(student.id),
                'personal_number': student.personal_number,
                'full_name': student.full_name,
                'phone_number': user.phone_number if user else None,
                'email': user.email if user else None,
                'status': student.status,
                'status_display': student.get_status_display(),
            }
            
            # Current class
            if student.current_class:
                student_data['current_class'] = {
                    'id': str(student.current_class.id),
                    'name': student.current_class.name,
                }
            else:
                student_data['current_class'] = None
            
            # Avatar
            if user:
                profile = getattr(user, 'profile', None)
                if profile and profile.avatar:
                    try:
                        student_data['avatar'] = profile.avatar.url
                        request = self.context.get('request')
                        if request:
                            student_data['avatar_url'] = request.build_absolute_uri(profile.avatar.url)
                        else:
                            student_data['avatar_url'] = None
                    except:
                        student_data['avatar'] = None
                        student_data['avatar_url'] = None
                else:
                    student_data['avatar'] = None
                    student_data['avatar_url'] = None
            else:
                student_data['avatar'] = None
                student_data['avatar_url'] = None
            
            return student_data
        return None
    
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
    
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False
    )
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
        extra_kwargs = {
            'branch': {'required': False}
        }
        validators = []  # Custom validation
    
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
        student_profile: StudentProfile = validated_data.get('student_profile')
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
            description=f"O'quvchi to'lovi: {student_profile.user_branch.user.get_full_name()} {student_profile.current_class.name}",
            student_profile=student_profile,
            transaction_date=validated_data.get('payment_date', timezone.now()),
        )
        
        # MUHIM: Kassa balansini yangilash
        # Transaction.save() metodi objects.create() da ishlamasligi mumkin
        cash_register.update_balance(final_amount, TransactionType.PAYMENT)
        
        # To'lov yaratish
        validated_data['transaction'] = transaction
        payment = super().create(validated_data)
        
        # O'quvchi balansini yangilash
        student_balance, _ = StudentBalance.objects.get_or_create(
            student_profile=student_profile
        )
        student_balance.add_amount(final_amount)
        
        return payment


class StudentSubscriptionSerializer(serializers.ModelSerializer):
    """O'quvchi abonement serializer."""
    
    student_name = serializers.CharField(source='student_profile.full_name', read_only=True)
    subscription_plan_name = serializers.CharField(source='subscription_plan.name', read_only=True)
    subscription_plan_price = serializers.IntegerField(source='subscription_plan.price', read_only=True)
    period_display = serializers.CharField(source='subscription_plan.get_period_display', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    
    class Meta:
        model = StudentSubscription
        fields = [
            'id',
            'student_profile',
            'student_name',
            'subscription_plan',
            'subscription_plan_name',
            'subscription_plan_price',
            'period_display',
            'branch',
            'branch_name',
            'is_active',
            'start_date',
            'end_date',
            'next_payment_date',
            'total_debt',
            'last_payment_date',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_debt']


class StudentSubscriptionCreateSerializer(serializers.ModelSerializer):
    """O'quvchi abonement yaratish serializer."""
    
    class Meta:
        model = StudentSubscription
        fields = [
            'student_profile',
            'subscription_plan',
            'branch',
            'start_date',
            'end_date',
            'next_payment_date',
            'notes',
        ]
    
    def validate(self, attrs):
        """Validatsiya."""
        student_profile = attrs.get('student_profile')
        subscription_plan = attrs.get('subscription_plan')
        branch = attrs.get('branch')
        
        # Tekshirish: o'quvchi bu branchga tegishli bo'lishi kerak
        if student_profile.user_branch.branch_id != branch.id:
            raise serializers.ValidationError({
                'student_profile': "O'quvchi bu filialga tegishli emas."
            })
        
        # Tekshirish: tarif bu branch uchun mavjud bo'lishi kerak
        if subscription_plan.branch and subscription_plan.branch_id != branch.id:
            raise serializers.ValidationError({
                'subscription_plan': "Bu abonement tarifi bu filial uchun mavjud emas."
            })
        
        # Tekshirish: o'quvchida faol abonement bor-yo'qligini tekshirish
        existing = StudentSubscription.objects.filter(
            student_profile=student_profile,
            subscription_plan=subscription_plan,
            is_active=True,
            deleted_at__isnull=True
        ).exists()
        
        if existing:
            raise serializers.ValidationError({
                'subscription_plan': "O'quvchida bu abonement turi allaqachon mavjud va faol."
            })
        
        return attrs


class PaymentDueSummarySerializer(serializers.Serializer):
    """O'quvchi to'lov xulosa serializer.
    
    O'quvchi qancha to'lashi kerakligini ko'rsatadi.
    """
    
    # O'quvchi ma'lumotlari
    student_profile_id = serializers.UUIDField()
    student_name = serializers.CharField()
    
    # Abonement ma'lumotlari
    subscription_id = serializers.UUIDField()
    subscription_plan_name = serializers.CharField()
    subscription_period = serializers.CharField()
    subscription_price = serializers.IntegerField()
    
    # To'lov ma'lumotlari
    current_amount = serializers.IntegerField(help_text="Joriy davr uchun summa")
    debt_amount = serializers.IntegerField(help_text="Qarz summasi")
    total_amount = serializers.IntegerField(help_text="Jami to'lanishi kerak")
    
    # Sana ma'lumotlari
    next_due_date = serializers.DateField(help_text="Keyingi to'lov sanasi")
    last_payment_date = serializers.DateField(allow_null=True, help_text="Oxirgi to'lov sanasi")
    overdue_months = serializers.IntegerField(help_text="Necha oy kechikkan")
    
    # Holat
    is_expired = serializers.BooleanField(help_text="Abonement tugaganmi?")
    is_overdue = serializers.BooleanField(help_text="To'lov kechiktirganmi?")

