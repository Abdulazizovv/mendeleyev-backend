from __future__ import annotations

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
        return obj.memberships.filter(deleted_at__isnull=True).count()


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
