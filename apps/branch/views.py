from __future__ import annotations

from typing import Iterable
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Branch, BranchStatuses, BranchMembership, Role
from .serializers import (
    BranchListSerializer,
    RoleSerializer,
    RoleCreateSerializer,
    BranchMembershipDetailSerializer,
    BalanceUpdateSerializer,
)
from auth.users.models import User
from apps.common.permissions import HasBranchRole, IsSuperAdmin, IsBranchAdmin


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


class RoleListView(ListCreateAPIView):
	"""List and create roles for a branch.
	
	- SuperAdmin: can create roles for any branch
	- BranchAdmin: can create roles only for their own branch
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	serializer_class = RoleSerializer
	
	def get_queryset(self):
		"""Get roles for the specified branch."""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if user.is_superuser:
			# SuperAdmin can see all roles
			return Role.objects.filter(branch=branch)
		else:
			# BranchAdmin can only see roles for their branch
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if membership:
				return Role.objects.filter(branch=branch)
			return Role.objects.none()
	
	def get_serializer_class(self):
		"""Use different serializer for create."""
		if self.request.method == 'POST':
			return RoleCreateSerializer
		return RoleSerializer
	
	def perform_create(self, serializer):
		"""Set branch and created_by on role creation."""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if not user.is_superuser:
			# BranchAdmin can only create roles for their branch
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if not membership:
				from rest_framework.exceptions import PermissionDenied
				raise PermissionDenied("You can only create roles for your own branch.")
		
		serializer.save(branch=branch, created_by=user, updated_by=user)
	
	@extend_schema(
		summary="List roles for a branch",
		parameters=[
			OpenApiParameter('branch_id', type=str, location=OpenApiParameter.PATH, description='Branch ID'),
		],
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)
	
	@extend_schema(
		summary="Create a new role for a branch",
		request=RoleCreateSerializer,
		responses={201: RoleSerializer},
	)
	def post(self, request, *args, **kwargs):
		return super().post(request, *args, **kwargs)


class RoleDetailView(RetrieveUpdateDestroyAPIView):
	"""Retrieve, update, or delete a role.
	
	- SuperAdmin: can manage any role
	- BranchAdmin: can manage roles only for their own branch
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	serializer_class = RoleSerializer
	lookup_field = 'id'
	
	def get_queryset(self):
		"""Get roles for the specified branch."""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if user.is_superuser:
			return Role.objects.filter(branch=branch)
		else:
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if membership:
				return Role.objects.filter(branch=branch)
			return Role.objects.none()
	
	def perform_update(self, serializer):
		"""Set updated_by on role update."""
		serializer.save(updated_by=self.request.user)
	
	@extend_schema(
		summary="Get role details",
		parameters=[
			OpenApiParameter('branch_id', type=str, location=OpenApiParameter.PATH),
			OpenApiParameter('id', type=str, location=OpenApiParameter.PATH),
		],
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)
	
	@extend_schema(
		summary="Update a role",
		request=RoleCreateSerializer,
		responses={200: RoleSerializer},
	)
	def patch(self, request, *args, **kwargs):
		return super().patch(request, *args, **kwargs)
	
	@extend_schema(
		summary="Delete a role",
		responses={204: None},
	)
	def delete(self, request, *args, **kwargs):
		return super().delete(request, *args, **kwargs)


class MembershipListView(ListCreateAPIView):
	"""List memberships for a branch.
	
	- SuperAdmin: can see all memberships
	- BranchAdmin: can see memberships for their branch
	
	Note: POST (create) is not implemented - memberships should be created via admin or separate endpoint.
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	serializer_class = BranchMembershipDetailSerializer
	
	def get_queryset(self):
		"""Get memberships for the specified branch."""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if user.is_superuser:
			return BranchMembership.objects.filter(branch=branch)
		else:
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if membership:
				return BranchMembership.objects.filter(branch=branch)
			return BranchMembership.objects.none()
	
	def post(self, request, *args, **kwargs):
		"""Create membership is not allowed via this endpoint."""
		return Response(
			{"detail": "Membership creation is not supported via this endpoint. Use admin panel or separate endpoint."},
			status=status.HTTP_405_METHOD_NOT_ALLOWED
		)
	
	@extend_schema(
		summary="List memberships for a branch",
		parameters=[
			OpenApiParameter('branch_id', type=str, location=OpenApiParameter.PATH),
		],
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)


class BalanceUpdateView(APIView):
	"""Update membership balance.
	
	- SuperAdmin: can update any membership balance
	- BranchAdmin: can update memberships for their branch
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	
	@extend_schema(
		summary="Update membership balance",
		request=BalanceUpdateSerializer,
		responses={200: BranchMembershipDetailSerializer},
		parameters=[
			OpenApiParameter('branch_id', type=str, location=OpenApiParameter.PATH),
			OpenApiParameter('membership_id', type=str, location=OpenApiParameter.PATH),
		],
	)
	def post(self, request, branch_id, membership_id):
		"""Add or subtract from membership balance."""
		branch = get_object_or_404(Branch, id=branch_id)
		membership = get_object_or_404(BranchMembership, id=membership_id, branch=branch)
		
		# Check permissions
		user = request.user
		if not user.is_superuser:
			admin_membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if not admin_membership:
				return Response(
					{"detail": "You can only update balances for your own branch."},
					status=status.HTTP_403_FORBIDDEN
				)
		
		serializer = BalanceUpdateSerializer(data=request.data)
		if serializer.is_valid():
			amount = Decimal(str(serializer.validated_data['amount']))
			
			if amount > 0:
				membership.add_to_balance(amount)
			elif amount < 0:
				success = membership.subtract_from_balance(abs(amount))
				if not success:
					return Response(
						{"detail": "Insufficient balance."},
						status=status.HTTP_400_BAD_REQUEST
					)
			
			# Update updated_by
			membership.updated_by = user
			membership.save(update_fields=['updated_by'])
			
			response_serializer = BranchMembershipDetailSerializer(membership)
			return Response(response_serializer.data, status=status.HTTP_200_OK)
		
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
