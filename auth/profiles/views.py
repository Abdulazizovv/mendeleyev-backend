from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .serializers import ProfileSerializer, UserBranchProfileSerializer


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @extend_schema(responses=ProfileSerializer, summary="Get current user's global profile")
    def get(self, request):
        prof = request.user.profile  # created by signal
        return Response(ProfileSerializer(prof).data)

    @extend_schema(request=ProfileSerializer, responses=ProfileSerializer, summary="Update current user's global profile")
    def patch(self, request):
        prof = request.user.profile
        ser = ProfileSerializer(prof, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


class MyBranchProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserBranchProfileSerializer, summary="Get role-aware profile for my membership in a branch")
    def get(self, request, branch_id: str):
        # Resolve the user's membership
        from apps.branch.models import BranchMembership
        m = BranchMembership.for_user_and_branch(request.user.id, branch_id)
        if not m:
            return Response({"detail": "No membership in this branch"}, status=status.HTTP_403_FORBIDDEN)
        # Role profile
        rp = getattr(m, "role_profile", None)
        if not rp:
            return Response({"detail": "No role profile yet"}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserBranchProfileSerializer(rp).data)

    @extend_schema(request=UserBranchProfileSerializer, responses=UserBranchProfileSerializer, summary="Create or update role-aware profile for my membership in a branch")
    def patch(self, request, branch_id: str):
        from apps.branch.models import BranchMembership
        from .models import UserBranchProfile

        m = BranchMembership.for_user_and_branch(request.user.id, branch_id)
        if not m:
            return Response({"detail": "No membership in this branch"}, status=status.HTTP_403_FORBIDDEN)

        rp = getattr(m, "role_profile", None)
        if not rp:
            rp = UserBranchProfile.objects.create(user_branch=m)
        ser = UserBranchProfileSerializer(rp, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)
