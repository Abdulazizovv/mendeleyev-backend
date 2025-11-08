from __future__ import annotations

from rest_framework import serializers
from .models import Profile, UserBranchProfile, Gender


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
