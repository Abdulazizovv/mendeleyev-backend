from __future__ import annotations

from rest_framework import serializers
from .models import (
    Profile,
    UserBranchProfile,
    Gender,
    TeacherProfile,
    StudentProfile,
    ParentProfile,
    AdminProfile,
)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "id",
            "avatar",
            "date_of_birth",
            "gender",
            "language",
            "timezone",
            "bio",
            "address",
            "socials",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class UserBranchProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBranchProfile
        fields = (
            "id",
            "display_name",
            "title",
            "about",
            "contacts",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = (
            "subject",
            "experience_years",
            "bio",
        )


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = (
            "grade",
            "enrollment_date",
            "parent_name",
        )


class ParentProfileSerializer(serializers.ModelSerializer):
    related_students = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = ParentProfile
        fields = (
            "notes",
            "related_students",
        )


class AdminProfileSerializer(serializers.ModelSerializer):
    """Serialize admin profile with a compact branch list for managed_branches.

    We intentionally expose managed_branches as a list of {id, name} objects for ease of use in UI.
    """

    managed_branches = serializers.SerializerMethodField()

    class Meta:
        model = AdminProfile
        fields = (
            "is_super_admin",
            "managed_branches",
            "title",
            "notes",
        )

    def get_managed_branches(self, obj: AdminProfile):
        try:
            items = obj.managed_branches.all()
            return [{"id": b.id, "name": getattr(b, "name", "")} for b in items]
        except Exception:
            return []
