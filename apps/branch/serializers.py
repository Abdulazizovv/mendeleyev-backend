from __future__ import annotations

from rest_framework import serializers

from .models import Branch, Role, BranchMembership


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "status", "type"]


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)
    
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
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


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
    salary = serializers.IntegerField(source='monthly_salary', read_only=True)
    
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
            "monthly_salary",
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
