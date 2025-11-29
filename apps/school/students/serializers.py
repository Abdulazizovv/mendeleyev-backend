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
            from apps.school.finance.models import SubscriptionPlan, Payment, Transaction, CashRegister
            from django.utils import timezone
            from datetime import timedelta
            
            subscription_plan = SubscriptionPlan.objects.get(id=subscription_plan_id)
            branch = membership.branch
            
            # Kassa topish yoki yaratish
            cash_register = CashRegister.objects.filter(
                branch=branch,
                is_active=True,
                deleted_at__isnull=True
            ).first()
            
            if not cash_register:
                # Agar kassa bo'lmasa, birinchi kassani yaratamiz
                cash_register = CashRegister.objects.create(
                    branch=branch,
                    name="Asosiy kassa",
                    is_active=True
                )
            
            # Davr boshlanish va tugash sanalarini hisoblash
            now = timezone.now()
            period = subscription_plan.period
            
            if period == 'monthly':
                period_start = now.date()
                period_end = (now + timedelta(days=30)).date()
            elif period == 'quarterly':
                period_start = now.date()
                period_end = (now + timedelta(days=90)).date()
            elif period == 'semester':
                period_start = now.date()
                period_end = (now + timedelta(days=180)).date()
            elif period == 'yearly':
                period_start = now.date()
                period_end = (now + timedelta(days=365)).date()
            else:
                period_start = now.date()
                period_end = (now + timedelta(days=30)).date()
            
            # Tranzaksiya yaratish
            transaction = Transaction.objects.create(
                branch=branch,
                cash_register=cash_register,
                transaction_type='payment',
                status='completed',
                amount=subscription_plan.price,
                payment_method='cash',
                description=f"O'quvchi abonement to'lovi: {subscription_plan.name}",
                student_profile=student_profile,
            )
            
            # Payment yaratish
            Payment.objects.create(
                student_profile=student_profile,
                branch=branch,
                subscription_plan=subscription_plan,
                base_amount=subscription_plan.price,
                discount_amount=0,
                final_amount=subscription_plan.price,
                payment_method='cash',
                period=period,
                payment_date=now,
                period_start=period_start,
                period_end=period_end,
                transaction=transaction,
                notes=f"O'quvchi yaratilganda abonement tanlandi"
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
            'date_of_birth',
            'address',
            'birth_certificate',
            'additional_fields',
            'current_class',
            'relatives_count',
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


class StudentRelativeSerializer(serializers.ModelSerializer):
    """O'quvchi yaqini serializer."""
    
    full_name = serializers.CharField(read_only=True)
    relationship_type_display = serializers.CharField(source='get_relationship_type_display', read_only=True)
    student_name = serializers.CharField(source='student_profile.full_name', read_only=True)
    
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
            'is_primary_contact',
            'is_guardian',
            'additional_info',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')


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

