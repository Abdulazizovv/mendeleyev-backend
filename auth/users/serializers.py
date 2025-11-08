from __future__ import annotations

from django.core.validators import RegexValidator
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from auth.users.models import UserBranch
from apps.branch.models import Branch


PHONE_VALIDATOR = RegexValidator(r"^\+?[0-9]{7,15}$", "Telefon raqami noto'g'ri formatda")


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    code = serializers.CharField(min_length=4, max_length=10)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = [
            "id",
            "phone_number",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "date_joined",
        ]


class RegisterRequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])


class RegisterConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    code = serializers.CharField(min_length=4, max_length=10)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value: str):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    password = serializers.CharField(write_only=True)
    branch_id = serializers.UUIDField(required=False, allow_null=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    code = serializers.CharField(min_length=4, max_length=10)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str):
        validate_password(value)
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str):
        validate_password(value)
        return value


class PhoneCheckSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])


class PhoneVerificationRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])


class PhoneVerificationConfirmSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    code = serializers.CharField(min_length=4, max_length=10)


class PasswordSetSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20, validators=[PHONE_VALIDATOR])
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value: str):
        validate_password(value)
        return value


class SwitchBranchSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    branch_id = serializers.UUIDField()


class BranchMembershipSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    branch_name = serializers.CharField()
    branch_type = serializers.CharField()
    branch_status = serializers.CharField()
    role = serializers.CharField()
    title = serializers.CharField(allow_blank=True)

    @staticmethod
    def from_userbranch(m: UserBranch) -> dict:
        b: Branch = m.branch
        return {
            "branch_id": b.id,
            "branch_name": getattr(b, "name", ""),
            "branch_type": getattr(b, "type", ""),
            "branch_status": getattr(b, "status", ""),
            "role": m.role,
            "title": m.title or "",
        }
