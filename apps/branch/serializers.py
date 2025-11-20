from __future__ import annotations

from rest_framework import serializers
from decimal import Decimal

from .models import Branch, Role, BranchMembership, SalaryType


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "status", "type"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)
    salary = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "branch",
            "branch_name",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_item_rate",
            "salary",
            "permissions",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
    
    def get_salary(self, obj):
        """Get current salary based on salary_type."""
        return float(obj.get_salary()) if obj.get_salary() else 0


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new role."""
    
    class Meta:
        model = Role
        fields = [
            "name",
            "branch",
            "salary_type",
            "monthly_salary",
            "hourly_rate",
            "per_item_rate",
            "permissions",
            "description",
            "is_active",
        ]
    
    def validate(self, data):
        """Validate salary fields based on salary_type."""
        salary_type = data.get('salary_type', SalaryType.MONTHLY)
        
        if salary_type == SalaryType.MONTHLY:
            if not data.get('monthly_salary'):
                raise serializers.ValidationError({
                    "monthly_salary": "Oylik maosh belgilanishi kerak."
                })
        elif salary_type == SalaryType.HOURLY:
            if not data.get('hourly_rate'):
                raise serializers.ValidationError({
                    "hourly_rate": "Soatlik stavka belgilanishi kerak."
                })
        elif salary_type == SalaryType.PER_ITEM:
            if not data.get('per_item_rate'):
                raise serializers.ValidationError({
                    "per_item_rate": "Har bir uchun stavka belgilanishi kerak."
                })
        
        return data


class BranchMembershipDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for BranchMembership (admin use)."""
    
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    role_name = serializers.CharField(source='role_ref.name', read_only=True, allow_null=True)
    effective_role = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()
    
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
            "balance",
            "salary",
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
        """Get salary from role."""
        return float(obj.get_salary()) if obj.get_salary() else 0


class BalanceUpdateSerializer(serializers.Serializer):
    """Serializer for updating membership balance."""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Qo'shish uchun musbat, ayirish uchun manfiy qiymat"
    )
    note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Balans o'zgarishi sababi"
    )
