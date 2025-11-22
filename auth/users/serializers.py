from __future__ import annotations

from django.core.validators import RegexValidator
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from apps.branch.models import BranchMembership
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
    effective_role = serializers.CharField(required=False, allow_null=True)
    role_ref_id = serializers.UUIDField(required=False, allow_null=True)
    salary_type = serializers.CharField(required=False, allow_null=True, help_text="Maosh turi: monthly/hourly/per_lesson")
    salary = serializers.IntegerField(required=False, allow_null=True, help_text="Maosh (salary_type ga qarab)")
    balance = serializers.IntegerField(required=False, allow_null=True, help_text="Balans (so'm, butun son)")
    title = serializers.CharField(allow_blank=True)
    role_data = serializers.SerializerMethodField()

    def get_role_data(self, obj):  # obj is dict produced by from_membership OR membership instance
        # Support both raw BranchMembership/UserBranch instance and dict built below for backward compatibility.
        membership = obj.get('_membership') if isinstance(obj, dict) else obj
        try:
            from auth.profiles.serializers import (
                TeacherProfileSerializer,
                StudentProfileSerializer,
                ParentProfileSerializer,
                AdminProfileSerializer,
            )
        except Exception:
            return None
        try:
            # When called with dict created by from_membership we attached actual membership under _membership
            role = membership.role
            if role == 'teacher' and hasattr(membership, 'teacher_profile'):
                return TeacherProfileSerializer(membership.teacher_profile).data
            if role == 'student' and hasattr(membership, 'student_profile'):
                return StudentProfileSerializer(membership.student_profile).data
            if role == 'parent' and hasattr(membership, 'parent_profile'):
                return ParentProfileSerializer(membership.parent_profile).data
            if role in ('branch_admin', 'super_admin') and hasattr(membership, 'admin_profile'):
                # Always serialize AdminProfile for admin-class roles
                return AdminProfileSerializer(membership.admin_profile).data
            return None
        except Exception:
            return None

    @staticmethod
    def from_membership(m: BranchMembership) -> dict:
        """Static constructor including role_data for a membership instance.

        Returns a plain JSON-serializable dict suitable for direct Response usage.
        """
        b: Branch = m.branch
        data = {
            "branch_id": b.id,
            "branch_name": getattr(b, "name", ""),
            "branch_type": getattr(b, "type", ""),
            "branch_status": getattr(b, "status", ""),
            "role": m.role,
            "effective_role": m.get_effective_role(),
            "role_ref_id": str(m.role_ref.id) if m.role_ref else None,
            "salary_type": m.salary_type,
            "salary": m.get_salary() if m.get_salary() else None,
            "balance": m.balance if m.balance else 0,
            "title": m.title or "",
        }
    # Dynamically attach role_data now (optional convenience); serializer will also compute.
        try:
            from auth.profiles.serializers import (
                TeacherProfileSerializer,
                StudentProfileSerializer,
                ParentProfileSerializer,
                AdminProfileSerializer,
            )
            if m.role == 'teacher' and hasattr(m, 'teacher_profile'):
                data['role_data'] = TeacherProfileSerializer(m.teacher_profile).data
            elif m.role == 'student' and hasattr(m, 'student_profile'):
                data['role_data'] = StudentProfileSerializer(m.student_profile).data
            elif m.role == 'parent' and hasattr(m, 'parent_profile'):
                data['role_data'] = ParentProfileSerializer(m.parent_profile).data
            elif m.role in ('branch_admin', 'super_admin') and hasattr(m, 'admin_profile'):
                data['role_data'] = AdminProfileSerializer(m.admin_profile).data
        except Exception:
            pass
        return data

    # Backward-compatible alias
    from_userbranch = from_membership


class MeResponseSerializer(serializers.Serializer):
    """Composite serializer for /auth/me endpoint.

    We intentionally keep it lightweight (Serializer rather than ModelSerializer) since
    the response aggregates multiple sources (User, Profile, BranchMembership proxy + role profiles).

    All nested serializers are read-only; input validation is not required for GET.
    """

    user = UserSerializer(read_only=True)
    profile = serializers.DictField(allow_null=True)  # We serialize via ProfileSerializer externally.
    current_branch = BranchMembershipSerializer(allow_null=True, required=False)
    memberships = BranchMembershipSerializer(many=True)
    auth_state = serializers.CharField()

    class Meta:
        fields = ["user", "profile", "current_branch", "memberships", "auth_state"]
