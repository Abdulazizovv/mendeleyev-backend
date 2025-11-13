from __future__ import annotations

from rest_framework import serializers

from .models import Branch


class BranchListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ["id", "name", "status"]
