from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.branch.models import BranchMembership, BranchRole
from apps.school.classes.models import Class
from auth.profiles.models import StudentProfile, StudentRelative

User = get_user_model()


class StudentCreateSerializer(serializers.Serializer):
    """O'quvchi yaratish uchun serializer.
    
    Bu serializer o'quvchi yaratishda ishlatiladi. Telefon raqam tasdiqlash shart emas.
    """
    # User ma'lumotlari
    phone_number = serializers.CharField(
        max_length=20,
        help_text='Telefon raqami (masalan: +998901234567)'
    )
    first_name = serializers.CharField(
        max_length=150,
        help_text='Ism'
    )
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        default='',
        help_text='Familiya'
    )
    email = serializers.EmailField(
        required=False,
        allow_null=True,
        help_text='Email manzili'
    )
    password = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text='Parol (ixtiyoriy, agar berilmasa tasdiqlanmagan hisoblanadi)'
    )
    
    # Branch ma'lumotlari
    branch_id = serializers.UUIDField(
        help_text='Filial ID'
    )
    
    # StudentProfile ma'lumotlari
    middle_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        default='',
        help_text='Otasining ismi'
    )
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', 'unspecified'],
        required=False,
        default='unspecified',
        help_text='Jinsi'
    )
    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
        help_text='Tu\'gilgan sana (YYYY-MM-DD)'
    )
    address = serializers.CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text='Manzil'
    )
    additional_fields = serializers.JSONField(
        required=False,
        allow_null=True,
        default=dict,
        help_text='Qo\'shimcha ma\'lumotlar JSON formatida'
    )
    
    # Sinfga biriktirish (ixtiyoriy)
    class_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='Sinf ID (agar o\'quvchini sinfga biriktirish kerak bo\'lsa)'
    )
    
    # Abonement tanlash (ixtiyoriy)
    subscription_plan_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='Abonement tarifi ID (agar o\'quvchiga abonement tanlash kerak bo\'lsa)'
    )
    subscription_start_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text='Abonement boshlanish sanasi (agar berilmasa, bugungi sana qo\'llaniladi)'
    )
    subscription_next_payment_date = serializers.DateField(
        required=False,
        allow_null=True,
        help_text='Keyingi to\'lov sanasi (agar berilmasa, avtomatik hisoblanadi)'
    )
    discount_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='Chegirma ID (ixtiyoriy, abonementga chegirma qo\'llash uchun)'
    )
    
    # Hujjat ma'lumotlari
    birth_certificate = serializers.FileField(
        required=False,
        allow_null=True,
        help_text='Tu\'gilganlik guvohnoma rasmi (PDF yoki rasm)'
    )
    passport_number = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default='',
        help_text='Pasport yoki ID karta raqami'
    )
    nationality = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default='',
        help_text='Millati (masalan: UZ, RU)'
    )
    
    # Yaqinlar (nested serializer)
    relatives = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        help_text='O\'quvchi yaqinlari ro\'yxati'
    )
    
    def validate(self, attrs):
        """Umumiy validatsiya."""
        phone_number = attrs.get('phone_number')
        branch_id = attrs.get('branch_id')
        
        if phone_number and branch_id:
            # Normalize phone number
            normalized = str(phone_number).strip().replace(" ", "")
            attrs['phone_number'] = normalized
            
            # User mavjudligini tekshirish
            user = User.objects.filter(phone_number=normalized).first()
            if user:
                # Bu branchda allaqachon student bo'lishi mumkin
                from apps.branch.models import BranchMembership, BranchRole
                existing_membership = BranchMembership.objects.filter(
                    user=user,
                    branch_id=branch_id,
                    role=BranchRole.STUDENT,
                    deleted_at__isnull=True
                ).first()
                if existing_membership:
                    raise serializers.ValidationError({
                        'phone_number': "Bu telefon raqami allaqachon bu filialda o'quvchi sifatida ro'yxatdan o'tgan."
                    })
        
        return attrs
    
    def validate_phone_number(self, value):
        """Telefon raqamini tekshirish."""
        # Normalize phone number
        normalized = str(value).strip().replace(" ", "")
        return normalized
    
    def validate_branch_id(self, value):
        """Filialni tekshirish."""
        from apps.branch.models import Branch
        try:
            branch = Branch.objects.get(id=value, deleted_at__isnull=True)
            return value
        except Branch.DoesNotExist:
            raise serializers.ValidationError("Filial topilmadi.")
    
    def validate_class_id(self, value):
        """Sinfni tekshirish."""
        if value:
            try:
                class_obj = Class.objects.get(id=value, deleted_at__isnull=True)
                return value
            except Class.DoesNotExist:
                raise serializers.ValidationError("Sinf topilmadi.")
        return value
    
    def validate_subscription_plan_id(self, value):
        """Abonement tarifini tekshirish."""
        if value:
            from apps.school.finance.models import SubscriptionPlan
            try:
                plan = SubscriptionPlan.objects.get(id=value, deleted_at__isnull=True, is_active=True)
                return value
            except SubscriptionPlan.DoesNotExist:
                raise serializers.ValidationError("Abonement tarifi topilmadi yoki faol emas.")
        return value
    
    def validate_discount_id(self, value):
        """Chegirmani tekshirish."""
        if value:
            from apps.school.finance.models import Discount
            try:
                discount = Discount.objects.get(id=value, deleted_at__isnull=True, is_active=True)
                # Chegirma amal qilish muddatini tekshirish
                if not discount.is_valid():
                    raise serializers.ValidationError("Chegirma muddati tugagan yoki hali boshlanmagan.")
                return value
            except Discount.DoesNotExist:
                raise serializers.ValidationError("Chegirma topilmadi yoki faol emas.")
        return value
    
    def validate_relatives(self, value):
        """Yaqinlarni tekshirish."""
        if not value:
            return value
        
        required_fields = ['relationship_type', 'first_name', 'phone_number']
        for idx, relative in enumerate(value):
            for field in required_fields:
                if field not in relative or not relative[field]:
                    raise serializers.ValidationError({
                        'relatives': f"Yaqin #{idx + 1}: '{field}' maydoni majburiy."
                    })
        
        return value
    
    def create(self, validated_data):
        """O'quvchi yaratish."""
        # User yaratish yoki olish
        phone_number = validated_data['phone_number']
        first_name = validated_data['first_name']
        last_name = validated_data.get('last_name', '')
        email = validated_data.get('email')
        password = validated_data.get('password')
        
        user, user_created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone_verified': False,  # Telefon tasdiqlash shart emas
            }
        )
        
        # Agar user allaqachon mavjud bo'lsa, ma'lumotlarni yangilaymiz
        if not user_created:
            if first_name and not user.first_name:
                user.first_name = first_name
            if last_name and not user.last_name:
                user.last_name = last_name
            if email and not user.email:
                user.email = email
            user.save()
        
        # Parol o'rnatish (agar berilgan bo'lsa)
        if password:
            user.set_password(password)
            user.save()
        elif user_created:
            # Yangi user uchun unusable password
            user.set_unusable_password()
            user.save()
        
        # BranchMembership yaratish yoki olish
        branch_id = validated_data['branch_id']
        
        # Unique constraint (user, branch) bo'lgani uchun, barcha roldagi membershiplarni tekshiramiz
        existing_membership = BranchMembership.objects.filter(
            user=user,
            branch_id=branch_id
        ).first()
        
        if existing_membership:
            # Agar soft-deleted bo'lsa
            if existing_membership.deleted_at:
                # Agar soft-deleted va STUDENT roli bo'lsa, restore qilamiz
                if existing_membership.role == BranchRole.STUDENT:
                    existing_membership.deleted_at = None
                    existing_membership.save(update_fields=['deleted_at', 'updated_at'])
                    membership = existing_membership
                    membership_created = False
                else:
                    # Agar boshqa rolda bo'lsa, xatolik (rolni o'zgartirish kerak emas)
                    raise serializers.ValidationError({
                        'phone_number': f"Bu telefon raqami allaqachon bu filialda {existing_membership.get_role_display()} sifatida ro'yxatdan o'tgan. O'quvchi sifatida qo'shish mumkin emas."
                    })
            else:
                # Agar allaqachon faol bo'lsa
                if existing_membership.role == BranchRole.STUDENT:
                    # Agar allaqachon student bo'lsa, xatolik yuboramiz
                    raise serializers.ValidationError({
                        'phone_number': "Bu telefon raqami allaqachon bu filialda o'quvchi sifatida ro'yxatdan o'tgan."
                    })
                else:
                    # Agar boshqa rolda bo'lsa (masalan, PARENT, TEACHER), xatolik
                    # Chunki unique constraint tufayli yangi membership yaratib bo'lmaydi
                    raise serializers.ValidationError({
                        'phone_number': f"Bu telefon raqami allaqachon bu filialda {existing_membership.get_role_display()} sifatida ro'yxatdan o'tgan. O'quvchi sifatida qo'shish mumkin emas."
                    })
        else:
            # User o'sha branchda yo'q, yangi membership yaratish
            membership = BranchMembership.objects.create(
                user=user,
                branch_id=branch_id,
                role=BranchRole.STUDENT
            )
            membership_created = True
        
        # StudentProfile yaratish yoki yangilash
        # Signal avtomatik yaratishi mumkin, shuning uchun get_or_create ishlatamiz
        
        # Hujjat ma'lumotlarini additional_fields ga qo'shamiz
        additional_fields = validated_data.get('additional_fields', {}) or {}
        if validated_data.get('passport_number'):
            additional_fields['passport_number'] = validated_data.get('passport_number')
        if validated_data.get('nationality'):
            additional_fields['nationality'] = validated_data.get('nationality')
        
        student_profile, profile_created = StudentProfile.objects.get_or_create(
            user_branch=membership,
            defaults={
                'middle_name': validated_data.get('middle_name', ''),
                'gender': validated_data.get('gender', 'unspecified'),
                'date_of_birth': validated_data.get('date_of_birth'),
                'address': validated_data.get('address', ''),
                'birth_certificate': validated_data.get('birth_certificate'),
                'additional_fields': additional_fields,
            }
        )
        
        # Agar profil allaqachon mavjud bo'lsa, ma'lumotlarni yangilaymiz
        if not profile_created:
            update_fields = []
            if validated_data.get('middle_name'):
                student_profile.middle_name = validated_data.get('middle_name')
                update_fields.append('middle_name')
            if validated_data.get('gender'):
                student_profile.gender = validated_data.get('gender')
                update_fields.append('gender')
            if validated_data.get('date_of_birth'):
                student_profile.date_of_birth = validated_data.get('date_of_birth')
                update_fields.append('date_of_birth')
            if validated_data.get('address'):
                student_profile.address = validated_data.get('address')
                update_fields.append('address')
            if validated_data.get('birth_certificate'):
                student_profile.birth_certificate = validated_data.get('birth_certificate')
                update_fields.append('birth_certificate')
            
            # Additional fields ni yangilash
            existing_fields = student_profile.additional_fields or {}
            if validated_data.get('passport_number'):
                existing_fields['passport_number'] = validated_data.get('passport_number')
            if validated_data.get('nationality'):
                existing_fields['nationality'] = validated_data.get('nationality')
            if validated_data.get('additional_fields'):
                existing_fields.update(validated_data.get('additional_fields', {}))
            student_profile.additional_fields = existing_fields
            update_fields.append('additional_fields')
            
            if update_fields:
                student_profile.save(update_fields=update_fields)
        
        # Sinfga biriktirish (agar berilgan bo'lsa)
        class_id = validated_data.get('class_id')
        if class_id:
            from apps.school.classes.models import ClassStudent
            ClassStudent.objects.get_or_create(
                class_obj_id=class_id,
                membership=membership,
                defaults={'is_active': True}
            )
        
        # Abonement tanlash (agar berilgan bo'lsa)
        subscription_plan_id = validated_data.get('subscription_plan_id')
        if subscription_plan_id:
            from apps.school.finance.models import SubscriptionPlan, StudentSubscription, Discount
            from django.utils import timezone
            from dateutil.relativedelta import relativedelta
            from datetime import datetime
            
            subscription_plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
            branch = membership.branch
            
            # Start date'ni olish (agar berilgan bo'lsa)
            start_date = validated_data.get('subscription_start_date')
            if not start_date:
                start_date = timezone.now().date()
            
            # Next payment date'ni olish yoki hisoblash
            next_payment_date = validated_data.get('subscription_next_payment_date')
            if not next_payment_date:
                # Avtomatik hisoblash
                period = subscription_plan.period
                start_datetime = datetime.combine(start_date, datetime.min.time())
                
                if period == 'monthly':
                    next_payment_date = (start_datetime + relativedelta(months=1)).date()
                elif period == 'quarterly':
                    next_payment_date = (start_datetime + relativedelta(months=3)).date()
                elif period == 'yearly':
                    next_payment_date = (start_datetime + relativedelta(years=1)).date()
                else:
                    next_payment_date = (start_datetime + relativedelta(months=1)).date()
            
            # Chegirmani olish (agar berilgan bo'lsa)
            discount = None
            discount_id = validated_data.get('discount_id')
            if discount_id:
                try:
                    discount = Discount.objects.get(id=discount_id)
                except Discount.DoesNotExist:
                    pass
            
            # StudentSubscription yaratish
            StudentSubscription.objects.create(
                student_profile=student_profile,
                subscription_plan=subscription_plan,
                branch=branch,
                discount=discount,
                is_active=True,
                start_date=start_date,
                next_payment_date=next_payment_date,
                total_debt=0,
                notes=f"O'quvchi yaratilganda abonement biriktirildi"
            )
        
        # Yaqinlarni yaratish (agar berilgan bo'lsa)
        relatives_data = validated_data.get('relatives', [])
        if relatives_data:
            self._create_relatives(student_profile, membership.branch, relatives_data)
        
        return student_profile
    
    def _create_relatives(self, student_profile, branch, relatives_data):
        """Yaqinlarni yaratish va ularga user/parent membership yaratish."""
        from django.db import transaction as db_transaction
        from rest_framework.exceptions import ValidationError
        
        with db_transaction.atomic():
            for relative_data in relatives_data:
                # Yaqin uchun User yaratish yoki olish
                relative_phone = str(relative_data['phone_number']).strip().replace(" ", "")
                relative_user, user_created = User.objects.get_or_create(
                    phone_number=relative_phone,
                    defaults={
                        'first_name': relative_data.get('first_name', ''),
                        'last_name': relative_data.get('last_name', ''),
                        'email': relative_data.get('email'),
                        'phone_verified': False,
                    }
                )
                
                # Agar user allaqachon mavjud bo'lsa, ma'lumotlarni yangilaymiz
                if not user_created:
                    if relative_data.get('first_name') and not relative_user.first_name:
                        relative_user.first_name = relative_data.get('first_name')
                    if relative_data.get('last_name') and not relative_user.last_name:
                        relative_user.last_name = relative_data.get('last_name')
                    if relative_data.get('email') and not relative_user.email:
                        relative_user.email = relative_data.get('email')
                    relative_user.save()
                else:
                    # Yangi user uchun unusable password
                    relative_user.set_unusable_password()
                    relative_user.save()
                
                # Parent membership yaratish yoki olish
                existing_relative_membership = BranchMembership.objects.filter(
                    user=relative_user,
                    branch=branch
                ).first()
                
                if existing_relative_membership:
                    # Agar soft-deleted bo'lsa, restore qilamiz
                    if existing_relative_membership.deleted_at:
                        existing_relative_membership.deleted_at = None
                        existing_relative_membership.role = BranchRole.PARENT
                        existing_relative_membership.save(update_fields=['deleted_at', 'role', 'updated_at'])
                        relative_membership = existing_relative_membership
                    else:
                        # Agar faol bo'lsa va boshqa rolda bo'lsa, xatolik
                        if existing_relative_membership.role != BranchRole.PARENT:
                            from rest_framework.exceptions import ValidationError
                            raise ValidationError({
                                'relatives': f"Yaqin {relative_phone} allaqachon bu filialda {existing_relative_membership.get_role_display()} sifatida ro'yxatdan o'tgan."
                            })
                        relative_membership = existing_relative_membership
                else:
                    # Yangi membership yaratish
                    relative_membership = BranchMembership.objects.create(
                        user=relative_user,
                        branch=branch,
                        role=BranchRole.PARENT
                    )
                
                # StudentRelative yaratish
                StudentRelative.objects.create(
                    student_profile=student_profile,
                    relationship_type=relative_data['relationship_type'],
                    first_name=relative_data.get('first_name', ''),
                    last_name=relative_data.get('last_name', ''),
                    middle_name=relative_data.get('middle_name', ''),
                    phone_number=relative_phone,
                    email=relative_data.get('email'),
                    gender=relative_data.get('gender', 'unspecified'),
                    date_of_birth=relative_data.get('date_of_birth'),
                    address=relative_data.get('address', ''),
                    workplace=relative_data.get('workplace', ''),
                    position=relative_data.get('position', ''),
                    passport_number=relative_data.get('passport_number', ''),
                    photo=relative_data.get('photo'),
                    is_primary_contact=relative_data.get('is_primary_contact', False),
                    is_guardian=relative_data.get('is_guardian', False),
                    additional_info=relative_data.get('additional_info', {}),
                    notes=relative_data.get('notes', ''),
                )


class StudentRelativeCreateSerializer(serializers.ModelSerializer):
    """O'quvchi yaqini yaratish uchun serializer."""
    
    class Meta:
        model = StudentRelative
        fields = [
            'id',
            'student_profile',
            'relationship_type',
            'first_name',
            'middle_name',
            'last_name',
            'phone_number',
            'email',
            'gender',
            'date_of_birth',
            'address',
            'workplace',
            'position',
            'passport_number',
            'photo',
            'is_primary_contact',
            'is_guardian',
            'additional_info',
            'notes',
        ]
        read_only_fields = ('id',)


class StudentProfileSerializer(serializers.ModelSerializer):
    """O'quvchi profilini ko'rsatish uchun serializer."""
    
    user_id = serializers.UUIDField(source='user_branch.user.id', read_only=True)
    phone_number = serializers.CharField(source='user_branch.user.phone_number', read_only=True)
    first_name = serializers.CharField(source='user_branch.user.first_name', read_only=True)
    last_name = serializers.CharField(source='user_branch.user.last_name', read_only=True)
    email = serializers.EmailField(source='user_branch.user.email', read_only=True)
    branch_id = serializers.UUIDField(source='user_branch.branch.id', read_only=True)
    branch_name = serializers.CharField(source='user_branch.branch.name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    current_class = serializers.SerializerMethodField()
    relatives_count = serializers.SerializerMethodField()
    relatives = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    subscriptions = serializers.SerializerMethodField()
    payment_due = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    birth_certificate = serializers.SerializerMethodField()
    birth_certificate_url = serializers.SerializerMethodField()
    # Global avatar from user's Profile
    avatar = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    # Status and display
    status = serializers.CharField(read_only=True)
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'personal_number',
            'user_id',
            'phone_number',
            'first_name',
            'last_name',
            'middle_name',
            'full_name',
            'email',
            'branch_id',
            'branch_name',
            'gender',
            'status',
            'status_display',
            'date_of_birth',
            'address',
            'avatar',
            'avatar_url',
            'birth_certificate',
            'birth_certificate_url',
            'additional_fields',
            'current_class',
            'relatives_count',
            'relatives',
            'balance',
            'subscriptions',
            'payment_due',
            'recent_transactions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'personal_number', 'created_at', 'updated_at')
    
    def get_current_class(self, obj):
        """Joriy sinfni qaytarish."""
        current_class = obj.current_class
        if current_class:
            return {
                'id': str(current_class.id),
                'name': current_class.name,
                'academic_year': current_class.academic_year.name,
            }
        return None
    
    def get_relatives_count(self, obj):
        """Yaqinlar sonini qaytarish."""
        return obj.relatives.count()
    
    def get_relatives(self, obj):
        """Yaqinlar ro'yxatini qaytarish (detail view uchun)."""
        include_relatives = self.context.get('include_relatives', False)
        
        if include_relatives:
            relatives = obj.relatives.filter(deleted_at__isnull=True)
            return StudentRelativeSerializer(
                relatives, 
                many=True, 
                context=self.context
            ).data
        
        return None
    
    def get_birth_certificate(self, obj):
        """Tu'gilganlik guvohnoma rasmi nisbiy URL."""
        if obj.birth_certificate:
            # Faqat nisbiy URL qaytarish (MEDIA_URL bilan)
            return obj.birth_certificate.url
        return None
    
    def get_birth_certificate_url(self, obj):
        """Tu'gilganlik guvohnoma rasmi to'liq URL."""
        if obj.birth_certificate:
            request = self.context.get('request')
            if request:
                # request.build_absolute_uri() portni ham o'z ichiga oladi
                # Development va production uchun to'liq URL yaratish
                return request.build_absolute_uri(obj.birth_certificate.url)
            # Agar request bo'lmasa, nisbiy URL qaytarish
            return obj.birth_certificate.url
        return None

    def get_avatar(self, obj):
        """Global profil avatarining nisbiy URL."""
        profile = getattr(getattr(obj.user_branch.user, 'profile', None), 'avatar', None)
        if profile:
            try:
                return profile.url
            except Exception:
                return None
        return None

    def get_avatar_url(self, obj):
        """Global profil avatarining to'liq URL."""
        av = self.get_avatar(obj)
        if not av:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(av)
        return av

    def get_status_display(self, obj):
        try:
            return obj.get_status_display()
        except Exception:
            return obj.status
    
    def get_balance(self, obj):
        """O'quvchi balansini qaytarish."""
        include_finance_details = self.context.get('include_finance_details', False)
        
        try:
            # Balance OneToOne relation orqali olish
            balance = obj.balance
            
            if include_finance_details:
                # Detail view uchun to'liq ma'lumotlar
                from apps.school.finance.models import Transaction, Payment, TransactionType, TransactionStatus
                from django.db.models import Sum, Q
                
                # Tranzaksiyalar statistikasi
                transactions = Transaction.objects.filter(
                    student_profile=obj,
                    deleted_at__isnull=True,
                    status=TransactionStatus.COMPLETED
                )
                
                total_income = transactions.filter(
                    transaction_type__in=[TransactionType.INCOME, TransactionType.PAYMENT]
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                total_expense = transactions.filter(
                    transaction_type__in=[TransactionType.EXPENSE, TransactionType.SALARY, TransactionType.REFUND]
                ).aggregate(total=Sum('amount'))['total'] or 0
                
                transactions_count = transactions.count()
                
                # To'lovlar statistikasi
                payments = Payment.objects.filter(
                    student_profile=obj,
                    deleted_at__isnull=True
                ).order_by('-payment_date')
                
                total_payments = payments.aggregate(total=Sum('final_amount'))['total'] or 0
                payments_count = payments.count()
                
                last_payment = payments.first()
                last_payment_data = None
                if last_payment:
                    # Period display uchun
                    period_display = last_payment.period
                    try:
                        from apps.school.finance.models import SubscriptionPeriod
                        period_display = dict(SubscriptionPeriod.choices).get(last_payment.period, last_payment.period)
                    except:
                        pass
                    
                    last_payment_data = {
                        'id': str(last_payment.id),
                        'amount': last_payment.final_amount,
                        'date': last_payment.payment_date.isoformat() if last_payment.payment_date else None,
                        'period': last_payment.period,
                        'period_display': period_display,
                    }
                
                return {
                    'id': str(balance.id),
                    'balance': balance.balance,
                    'notes': balance.notes,
                    'updated_at': balance.updated_at.isoformat() if balance.updated_at else None,
                    'transactions_summary': {
                        'total_income': total_income,
                        'total_expense': total_expense,
                        'net_balance': total_income - total_expense,
                        'transactions_count': transactions_count,
                    },
                    'payments_summary': {
                        'total_payments': total_payments,
                        'payments_count': payments_count,
                        'last_payment': last_payment_data,
                    }
                }
            else:
                # List view uchun faqat balans summasi
                return {
                    'balance': balance.balance
                }
        except:
            # Agar balance bo'lmasa
            if include_finance_details:
                return {
                    'id': None,
                    'balance': 0,
                    'notes': '',
                    'updated_at': None,
                    'transactions_summary': {
                        'total_income': 0,
                        'total_expense': 0,
                        'net_balance': 0,
                        'transactions_count': 0,
                    },
                    'payments_summary': {
                        'total_payments': 0,
                        'payments_count': 0,
                        'last_payment': None,
                    }
                }
            else:
                return {
                    'balance': 0
                }
    
    def get_subscriptions(self, obj):
        """O'quvchi abonementlarini qaytarish (detail view uchun)."""
        include_subscriptions = self.context.get('include_subscriptions', False)
        
        if not include_subscriptions:
            return None
        
        try:
            from apps.school.finance.models import StudentSubscription
            
            subscriptions = StudentSubscription.objects.filter(
                student_profile=obj,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('subscription_plan', 'branch', 'discount').order_by('-created_at')
            
            result = []
            for subscription in subscriptions:
                subscription_data = {
                    'id': str(subscription.id),
                    'subscription_plan': {
                        'id': str(subscription.subscription_plan.id),
                        'name': subscription.subscription_plan.name,
                        'price': subscription.subscription_plan.price,
                        'period': subscription.subscription_plan.period,
                        'period_display': subscription.subscription_plan.get_period_display(),
                    },
                    'is_active': subscription.is_active,
                    'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
                    'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                    'next_payment_date': subscription.next_payment_date.isoformat() if subscription.next_payment_date else None,
                    'last_payment_date': subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
                    'total_debt': subscription.total_debt,
                    'notes': subscription.notes,
                    'created_at': subscription.created_at.isoformat() if subscription.created_at else None,
                }
                
                # Chegirma ma'lumotlarini qo'shish
                if subscription.discount:
                    subscription_data['discount'] = {
                        'id': str(subscription.discount.id),
                        'name': subscription.discount.name,
                        'discount_type': subscription.discount.discount_type,
                        'discount_type_display': subscription.discount.get_discount_type_display(),
                        'amount': subscription.discount.amount,
                        'is_active': subscription.discount.is_active,
                        'is_valid': subscription.discount.is_valid(),
                    }
                else:
                    subscription_data['discount'] = None
                
                result.append(subscription_data)
            
            return result
        except Exception as e:
            # Agar StudentSubscription modeli bo'lmasa yoki xatolik yuz bersa
            return []
    
    def get_payment_due(self, obj):
        """O'quvchi to'lov xulosasini qaytarish (detail view uchun)."""
        include_payment_due = self.context.get('include_payment_due', False)
        
        if not include_payment_due:
            return None
        
        try:
            from apps.school.finance.models import StudentSubscription
            from datetime import date
            
            # Faol abonementlarni olish
            subscriptions = StudentSubscription.objects.filter(
                student_profile=obj,
                is_active=True,
                deleted_at__isnull=True
            ).select_related('subscription_plan')
            
            if not subscriptions.exists():
                return {
                    'has_subscription': False,
                    'total_amount': 0,
                    'subscriptions': []
                }
            
            # Har bir abonement uchun to'lov xulosasini hisoblash
            today = date.today()
            total_amount = 0
            subscription_summaries = []
            
            for subscription in subscriptions:
                payment_due = subscription.calculate_payment_due()
                total_amount += payment_due['total_amount']
                
                summary = {
                    'subscription_id': str(subscription.id),
                    'subscription_plan_name': subscription.subscription_plan.name,
                    'subscription_period': subscription.subscription_plan.get_period_display(),
                    'subscription_price': subscription.subscription_plan.price,
                    'current_amount': payment_due['current_amount'],
                    'debt_amount': payment_due['debt_amount'],
                    'total_amount': payment_due['total_amount'],
                    'next_due_date': payment_due['next_due_date'].isoformat() if payment_due.get('next_due_date') else None,
                    'overdue_months': payment_due['overdue_months'],
                    'is_expired': payment_due['is_expired'],
                    'is_overdue': today > subscription.next_payment_date if subscription.next_payment_date else False,
                }
                
                # Chegirma ma'lumotlarini qo'shish
                if payment_due.get('has_discount'):
                    summary['discount_amount'] = payment_due['discount_amount']
                    summary['amount_after_discount'] = payment_due['amount_after_discount']
                    summary['has_discount'] = True
                else:
                    summary['discount_amount'] = 0
                    summary['amount_after_discount'] = payment_due['current_amount']
                    summary['has_discount'] = False
                
                subscription_summaries.append(summary)
            
            return {
                'has_subscription': True,
                'total_amount': total_amount,
                'subscriptions': subscription_summaries
            }
        except Exception as e:
            return {
                'has_subscription': False,
                'total_amount': 0,
                'subscriptions': [],
                'error': str(e)
            }
    
    def get_recent_transactions(self, obj):
        """O'quvchining oxirgi tranzaksiyalarini qaytarish (detail view uchun)."""
        include_recent_transactions = self.context.get('include_recent_transactions', False)
        
        if not include_recent_transactions:
            return None
        
        try:
            from apps.school.finance.models import Transaction, TransactionStatus
            
            # Oxirgi 10 ta tranzaksiyani olish
            transactions = Transaction.objects.filter(
                student_profile=obj,
                deleted_at__isnull=True
            ).select_related(
                'branch',
                'cash_register',
                'category',
                'employee_membership__user',
                'employee_membership__user__profile'
            ).order_by('-transaction_date')[:10]
            
            result = []
            for transaction in transactions:
                transaction_data = {
                    'id': str(transaction.id),
                    'transaction_type': transaction.transaction_type,
                    'transaction_type_display': transaction.get_transaction_type_display(),
                    'status': transaction.status,
                    'status_display': transaction.get_status_display(),
                    'amount': transaction.amount,
                    'payment_method': transaction.payment_method,
                    'payment_method_display': transaction.get_payment_method_display(),
                    'description': transaction.description,
                    'reference_number': transaction.reference_number,
                    'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                    'cash_register': {
                        'id': str(transaction.cash_register.id),
                        'name': transaction.cash_register.name,
                    } if transaction.cash_register else None,
                    'category': {
                        'id': str(transaction.category.id),
                        'name': transaction.category.name,
                        'type': transaction.category.type,
                    } if transaction.category else None,
                }
                
                # Xodim ma'lumotlarini qo'shish (agar mavjud bo'lsa)
                if transaction.employee_membership:
                    user = transaction.employee_membership.user
                    profile = getattr(user, 'profile', None)
                    
                    employee_data = {
                        'id': str(transaction.employee_membership.id),
                        'user_id': str(user.id),
                        'full_name': f"{user.first_name} {user.last_name}".strip(),
                        'phone_number': user.phone_number,
                        'role': transaction.employee_membership.role,
                        'role_display': transaction.employee_membership.get_role_display(),
                    }
                    
                    # Avatar qo'shish
                    if profile and profile.avatar:
                        try:
                            employee_data['avatar'] = profile.avatar.url
                        except:
                            employee_data['avatar'] = None
                    else:
                        employee_data['avatar'] = None
                    
                    transaction_data['employee'] = employee_data
                else:
                    transaction_data['employee'] = None
                
                result.append(transaction_data)
            
            return result
        except Exception as e:
            return []


class StudentRelativeSerializer(serializers.ModelSerializer):
    """O'quvchi yaqini serializer."""
    
    full_name = serializers.CharField(read_only=True)
    relationship_type_display = serializers.CharField(source='get_relationship_type_display', read_only=True)
    student_name = serializers.CharField(source='student_profile.full_name', read_only=True)
    photo = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = StudentRelative
        fields = [
            'id',
            'student_profile',
            'student_name',
            'relationship_type',
            'relationship_type_display',
            'first_name',
            'middle_name',
            'last_name',
            'full_name',
            'phone_number',
            'email',
            'gender',
            'date_of_birth',
            'address',
            'workplace',
            'position',
            'passport_number',
            'photo',
            'photo_url',
            'is_primary_contact',
            'is_guardian',
            'additional_info',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_photo(self, obj):
        """Yaqin rasmi nisbiy URL."""
        if obj.photo:
            # Faqat nisbiy URL qaytarish (MEDIA_URL bilan)
            return obj.photo.url
        return None
    
    def get_photo_url(self, obj):
        """Yaqin rasmi to'liq URL."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                # request.build_absolute_uri() portni ham o'z ichiga oladi
                # Development va production uchun to'liq URL yaratish
                return request.build_absolute_uri(obj.photo.url)
            # Agar request bo'lmasa, nisbiy URL qaytarish
            return obj.photo.url
        return None


class StudentDocumentsUpdateSerializer(serializers.Serializer):
    """O'quvchi hujjatlarini yangilash uchun serializer."""
    
    birth_certificate = serializers.FileField(
        required=False,
        allow_null=True,
        help_text='Tu\'gilganlik guvohnoma rasmi (PDF yoki rasm)'
    )
    passport_number = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text='Pasport yoki ID karta raqami'
    )
    nationality = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='Millati (masalan: UZ, RU)'
    )
    additional_fields = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text='Qo\'shimcha ma\'lumotlar JSON formatida'
    )
    
    def update(self, instance, validated_data):
        """Hujjatlar ma'lumotlarini yangilash."""
        update_fields = []
        
        if 'birth_certificate' in validated_data:
            instance.birth_certificate = validated_data['birth_certificate']
            update_fields.append('birth_certificate')
        
        # Additional fields ni yangilash
        if 'passport_number' in validated_data or 'nationality' in validated_data or 'additional_fields' in validated_data:
            existing_fields = instance.additional_fields or {}
            
            if 'passport_number' in validated_data:
                if validated_data['passport_number']:
                    existing_fields['passport_number'] = validated_data['passport_number']
                elif 'passport_number' in existing_fields:
                    del existing_fields['passport_number']
            
            if 'nationality' in validated_data:
                if validated_data['nationality']:
                    existing_fields['nationality'] = validated_data['nationality']
                elif 'nationality' in existing_fields:
                    del existing_fields['nationality']
            
            if 'additional_fields' in validated_data:
                existing_fields.update(validated_data['additional_fields'])
            
            instance.additional_fields = existing_fields
            update_fields.append('additional_fields')
        
        if update_fields:
            instance.save(update_fields=update_fields)
        
        return instance


class StudentUpdateSerializer(serializers.Serializer):
    """O'quvchi ma'lumotlarini yangilash uchun serializer.

    Barcha asosiy maydonlar, telefon raqami, profil rasmi (avatar) va hujjatlar
    (birth_certificate) ni bir so'rovda yangilashni qo'llab-quvvatlaydi.
    Multipart/form-data va JSON bilan ishlaydi.
    """

    # User fields
    phone_number = serializers.CharField(required=False, allow_blank=False)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)

    # Profile avatar
    avatar = serializers.FileField(required=False, allow_null=True)

    # StudentProfile fields
    middle_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=['male', 'female', 'other', 'unspecified'],
        required=False
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=['active', 'archived', 'suspended', 'graduated', 'transferred'],
        required=False
    )
    additional_fields = serializers.JSONField(required=False, allow_null=True)
    birth_certificate = serializers.FileField(required=False, allow_null=True)

    def validate_phone_number(self, value):
        normalized = str(value).strip().replace(' ', '')
        if not normalized:
            raise serializers.ValidationError("Telefon raqam noto'g'ri formatda.")
        return normalized

    def validate(self, attrs):
        """Telefon raqami unikalligini tekshirish va normalizatsiya."""
        instance: StudentProfile = self.instance
        user = instance.user_branch.user if instance else None

        phone_number = attrs.get('phone_number')
        if phone_number:
            normalized = self.validate_phone_number(phone_number)
            attrs['phone_number'] = normalized
            # Uniqueness across users except current
            qs = get_user_model().objects.filter(phone_number=normalized)
            if user:
                qs = qs.exclude(id=user.id)
            if qs.exists():
                raise serializers.ValidationError({'phone_number': "Bu telefon raqami allaqachon ishlatilmoqda."})

        return attrs

    def update(self, instance: StudentProfile, validated_data):
        """Apply changes to User, Profile and StudentProfile in one go."""
        user = instance.user_branch.user
        profile = getattr(user, 'profile', None)

        # Track update fields
        profile_updates = []
        student_updates = []
        user_updated = False

        # Update user fields
        for f in ('phone_number', 'first_name', 'last_name', 'email'):
            if f in validated_data:
                setattr(user, f, validated_data[f])
                user_updated = True
        if user_updated:
            user.save()

        # Update avatar
        if 'avatar' in validated_data:
            if profile is None:
                # Create profile lazily if missing
                from auth.profiles.models import Profile as GlobalProfile
                profile = GlobalProfile.objects.create(user=user)
            profile.avatar = validated_data['avatar']
            profile_updates.append('avatar')
        if profile_updates:
            profile.save(update_fields=profile_updates)

        # Update StudentProfile fields
        mapping_fields = [
            'middle_name', 'gender', 'date_of_birth', 'address', 'status',
        ]
        for f in mapping_fields:
            if f in validated_data:
                setattr(instance, f, validated_data[f])
                student_updates.append(f)

        # Merge additional_fields
        if 'additional_fields' in validated_data:
            existing = instance.additional_fields or {}
            add = validated_data['additional_fields'] or {}
            try:
                existing.update(add)
            except Exception:
                existing = add or {}
            instance.additional_fields = existing
            student_updates.append('additional_fields')

        # Birth certificate file
        if 'birth_certificate' in validated_data:
            instance.birth_certificate = validated_data['birth_certificate']
            student_updates.append('birth_certificate')

        if student_updates:
            instance.save(update_fields=student_updates)

        return instance


class UserCheckSerializer(serializers.Serializer):
    """User mavjudligini tekshirish uchun serializer."""
    phone_number = serializers.CharField(
        max_length=20,
        help_text='Telefon raqami (masalan: +998901234567)'
    )
    branch_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='Filial ID (ixtiyoriy, agar berilmasa barcha filiallarda qidiriladi)'
    )

