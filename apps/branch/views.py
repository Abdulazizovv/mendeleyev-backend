from __future__ import annotations

from typing import Iterable

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import Branch, BranchStatuses, BranchMembership
from .serializers import BranchListSerializer
from auth.users.models import User
from apps.common.permissions import HasBranchRole


class ManagedBranchesView(APIView):
	"""List and manage branches for admin-class users.

	- SuperAdmin role: global view of all ACTIVE branches; can PATCH managed list for a target admin user.
	- BranchAdmin role: view of only branches linked to their admin memberships (or managed list if set).
	- Others: 403.

	Note: We don't rely on HasBranchRole for branching here because this endpoint is not branch-scoped; we
	still include it for consistency but make role decisions explicitly using BranchMembership queries.
	"""

	permission_classes = [IsAuthenticated, HasBranchRole]

	def _is_super_admin(self, user: User) -> bool:
		return BranchMembership.objects.filter(user=user, role='super_admin').exists()

	def _is_branch_admin(self, user: User) -> bool:
		return BranchMembership.objects.filter(user=user, role='branch_admin').exists()

	@extend_schema(responses=BranchListSerializer, summary="List managed branches for current admin")
	def get(self, request):
		user: User = request.user
		if self._is_super_admin(user):
			# SuperAdmin: global list of ACTIVE branches
			branches = Branch.objects.filter(status=BranchStatuses.ACTIVE)
		elif self._is_branch_admin(user):
			# BranchAdmin: by default, branches from admin memberships
			admin_memberships = BranchMembership.objects.filter(user=user, role='branch_admin')
			# If any AdminProfile has managed_branches set, union them; else fallback to membership branches
			managed_union: set = set()
			for m in admin_memberships:
				ap = getattr(m, 'admin_profile', None)
				if ap:
					managed_union.update(ap.managed_branches.values_list('id', flat=True))
			if managed_union:
				branches = Branch.objects.filter(id__in=list(managed_union))
			else:
				branches = Branch.objects.filter(id__in=admin_memberships.values_list('branch_id', flat=True))
		else:
			return Response({"detail": "Not authorized"}, status=403)

		serializer = BranchListSerializer(branches, many=True)
		return Response(serializer.data)

	@extend_schema(request=None, responses={200: None}, summary="Update managed branches for an admin user (SuperAdmin only)")
	def patch(self, request):
		"""Allow only SuperAdmin to update managed branches list of a target admin user.

		Expected input: { "user_id": "<uuid>", "branch_ids": ["<uuid>", ...] }
		"""
		user: User = request.user
		if not self._is_super_admin(user):
			return Response({"detail": "Forbidden"}, status=403)

		user_id = request.data.get("user_id")
		branch_ids: Iterable[str] = request.data.get("branch_ids", [])
		target_user = get_object_or_404(User, id=user_id)

		# Ensure target user has an admin-class membership we can attach the profile to
		target_membership = (
			BranchMembership.objects.filter(user=target_user, role__in=['super_admin', 'branch_admin']).first()
		)
		if not target_membership:
			return Response({"detail": "Target user has no admin membership"}, status=400)

		# Only ACTIVE branches are allowed to be assigned
		branches = Branch.objects.filter(id__in=list(branch_ids), status=BranchStatuses.ACTIVE)

		# AdminProfile is per-membership; we attach the managed list to the chosen admin membership
		from auth.profiles.models import AdminProfile
		ap, _ = AdminProfile.objects.get_or_create(user_branch=target_membership)
		ap.managed_branches.set(branches)
		ap.save()

		return Response({"detail": "Managed branches updated successfully."})
