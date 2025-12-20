from __future__ import annotations

from typing import Iterable

from django.shortcuts import get_object_or_404
from django.db import models
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from .models import (
    Branch, BranchStatuses, BranchMembership, Role, BranchSettings, BranchRole,
    BalanceTransaction, SalaryPayment
)
from .serializers import (
    BranchListSerializer,
    RoleSerializer,
    RoleCreateSerializer,
    BranchMembershipDetailSerializer,
    BranchMembershipCreateSerializer,
    BalanceUpdateSerializer,
    StaffListSerializer,
    StaffDetailSerializer,
    StaffCreateSerializer,
    StaffUpdateSerializer,
    BranchSettingsSerializer,
    BalanceTransactionSerializer,
    SalaryPaymentSerializer,
    SalaryAccrualRequestSerializer,
    BalanceChangeRequestSerializer,
    SalaryPaymentRequestSerializer,
    SalaryCalculationSerializer,
    MonthlySalarySummarySerializer,
    BalanceTransactionListSerializer,
    SalaryPaymentListSerializer,
)
from .settings_serializers import (
    BranchSettingsSerializer,
    BranchSettingsUpdateSerializer,
)
from auth.users.models import User
from apps.common.permissions import HasBranchRole, IsSuperAdmin, IsBranchAdmin
from apps.common.mixins import AuditTrailMixin
from .services import BalanceService, SalaryCalculationService, SalaryPaymentService


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
		Note: branch_ids must be explicitly provided. Only the provided branch_ids will be set.
		"""
		user: User = request.user
		if not self._is_super_admin(user):
			return Response({"detail": "Forbidden"}, status=403)

		user_id = request.data.get("user_id")
		branch_ids = request.data.get("branch_ids")
		
		if user_id is None:
			return Response({"detail": "user_id is required"}, status=400)
		
		if branch_ids is None:
			return Response({"detail": "branch_ids is required"}, status=400)
		
		if not isinstance(branch_ids, list):
			return Response({"detail": "branch_ids must be a list"}, status=400)
		
		target_user = get_object_or_404(User, id=user_id)

		# Ensure target user has an admin-class membership we can attach the profile to
		target_membership = (
			BranchMembership.objects.filter(user=target_user, role__in=['super_admin', 'branch_admin']).first()
		)
		if not target_membership:
			return Response({"detail": "Target user has no admin membership"}, status=400)

		# Only ACTIVE branches are allowed to be assigned
		# Filter only the provided branch_ids (not all branches)
		branches = Branch.objects.filter(id__in=list(branch_ids), status=BranchStatuses.ACTIVE)
		
		# Check if all requested branches exist and are active
		if branches.count() != len(branch_ids):
			found_ids = set(branches.values_list('id', flat=True))
			requested_ids = set(branch_ids)
			missing = requested_ids - found_ids
			return Response({
				"detail": f"Some branches not found or not active: {list(missing)}"
			}, status=400)

		# AdminProfile is per-membership; we attach the managed list to the chosen admin membership
		from auth.profiles.models import AdminProfile
		ap, _ = AdminProfile.objects.get_or_create(user_branch=target_membership)
		# set() will replace all existing managed branches with the new list
		ap.managed_branches.set(branches)
		ap.save()

		return Response({
			"detail": "Managed branches updated successfully.",
			"managed_branches": [{"id": str(b.id), "name": b.name} for b in branches]
		})


class RoleListView(ListCreateAPIView):
	"""List and create roles for a branch.
	
	- SuperAdmin: can create roles for any branch
	- BranchAdmin: can create roles only for their own branch
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	serializer_class = RoleSerializer
	
	def get_queryset(self):
		"""Get roles for the specified branch.
		
		Includes:
		- Branch-specific roles (branch=branch)
		- Global roles (branch=None)
		"""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if user.is_superuser:
			# SuperAdmin can see all roles (branch-specific + global)
			return Role.objects.filter(
				models.Q(branch=branch) | models.Q(branch=None)
			).prefetch_related('role_memberships')
		else:
			# BranchAdmin can only see roles for their branch (branch-specific + global)
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if membership:
				return Role.objects.filter(
					models.Q(branch=branch) | models.Q(branch=None)
				).prefetch_related('role_memberships')
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
		"""Get roles for the specified branch.
		
		Includes:
		- Branch-specific roles (branch=branch)
		- Global roles (branch=None)
		"""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if user.is_superuser:
			return Role.objects.filter(
				models.Q(branch=branch) | models.Q(branch=None)
			).prefetch_related('role_memberships')
		else:
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if membership:
				return Role.objects.filter(
					models.Q(branch=branch) | models.Q(branch=None)
				).prefetch_related('role_memberships')
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
		summary="Delete a role (soft delete)",
		responses={204: None},
	)
	def delete(self, request, *args, **kwargs):
		"""Soft delete a role by setting is_active=False."""
		instance = self.get_object()
		
		# Check if role has active memberships
		active_memberships = instance.memberships.filter(deleted_at__isnull=True).count()
		if active_memberships > 0:
			return Response(
				{"detail": f"Bu roldan {active_memberships} ta xodim foydalanmoqda. Avval xodimlarni boshqa roliga o'tkazing."},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Soft delete: set is_active=False
		instance.is_active = False
		instance.updated_by = request.user
		instance.save(update_fields=['is_active', 'updated_by'])
		
		return Response(status=status.HTTP_204_NO_CONTENT)


class MembershipListView(ListCreateAPIView):
	"""List and create memberships for a branch.
	
	- SuperAdmin: can see and create memberships for any branch
	- BranchAdmin: can see memberships for their branch (create not allowed)
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	serializer_class = BranchMembershipDetailSerializer
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	# Filter by role, salary_type, is_active, user, branch, and ranges
	filterset_fields = {
		'role': ['exact', 'in'],
		'salary_type': ['exact', 'in'],
		'deleted_at': ['isnull'],
		'user__id': ['exact', 'in'],
		'user__phone_number': ['exact'],
		'branch__id': ['exact'],
		'balance': ['exact', 'lt', 'lte', 'gt', 'gte'],
		'created_at': ['date', 'date__lt', 'date__lte', 'date__gt', 'date__gte'],
		'updated_at': ['date', 'date__lt', 'date__lte', 'date__gt', 'date__gte'],
	}
	search_fields = ['user__first_name', 'user__last_name', 'user__phone_number', 'title']
	ordering_fields = ['created_at', 'updated_at', 'role', 'salary_type', 'balance']
	ordering = ['-created_at']
	
	def get_queryset(self):
		"""Get memberships for the specified branch."""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if user.is_superuser:
			return BranchMembership.objects.filter(branch=branch).select_related('user', 'branch', 'role_ref')
		else:
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if membership:
				return BranchMembership.objects.filter(branch=branch).select_related('user', 'branch', 'role_ref')
			return BranchMembership.objects.none()
	
	def get_serializer_class(self):
		"""Use different serializer for create."""
		if self.request.method == 'POST':
			return BranchMembershipCreateSerializer
		return BranchMembershipDetailSerializer
	
	def perform_create(self, serializer):
		"""Create membership - only SuperAdmin can create."""
		if not self.request.user.is_superuser:
			from rest_framework.exceptions import PermissionDenied
			raise PermissionDenied("Only SuperAdmin can create memberships via API.")
		
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		serializer.save(branch=branch, created_by=self.request.user, updated_by=self.request.user)
	
	@extend_schema(
		summary="List memberships for a branch",
		parameters=[
			OpenApiParameter('branch_id', type=str, location=OpenApiParameter.PATH),
			OpenApiParameter('role', type=str, location=OpenApiParameter.QUERY, description='Filter by role (e.g., teacher, student, branch_admin)'),
			OpenApiParameter('salary_type', type=str, location=OpenApiParameter.QUERY, description='Filter by salary type (monthly, hourly, per_lesson)'),
			OpenApiParameter('user_id', type=str, location=OpenApiParameter.QUERY, description='Filter by user UUID'),
			OpenApiParameter('is_active', type=bool, location=OpenApiParameter.QUERY, description='Filter active memberships (deleted_at is null)'),
			OpenApiParameter('search', type=str, location=OpenApiParameter.QUERY, description='Search by user name or phone, and membership title'),
			OpenApiParameter('ordering', type=str, location=OpenApiParameter.QUERY, description='Order by fields: created_at, updated_at, role, salary_type, balance'),
		],
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)
	
	@extend_schema(
		summary="Create a new membership (SuperAdmin only)",
		request=BranchMembershipCreateSerializer,
		responses={201: BranchMembershipDetailSerializer},
	)
	def post(self, request, *args, **kwargs):
		return super().post(request, *args, **kwargs)
	
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
			amount = serializer.validated_data['amount']
			
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


class BranchSettingsView(AuditTrailMixin, RetrieveUpdateAPIView):
	"""Filial sozlamalari.
	
	- SuperAdmin: istalgan filial sozlamalarini ko'rish va yangilash
	- BranchAdmin: faqat o'z filial sozlamalarini ko'rish va yangilash
	"""
	
	permission_classes = [IsAuthenticated, HasBranchRole]
	required_branch_roles = ("branch_admin", "super_admin")
	serializer_class = BranchSettingsSerializer
	lookup_url_kwarg = 'branch_id'
	lookup_field = 'branch_id'
	
	def get_object(self):
		"""Get or create branch settings."""
		branch_id = self.kwargs.get('branch_id')
		branch = get_object_or_404(Branch, id=branch_id)
		
		# Check permissions
		user = self.request.user
		if not user.is_superuser:
			membership = BranchMembership.objects.filter(
				user=user,
				branch=branch,
				role__in=['branch_admin', 'super_admin']
			).first()
			if not membership:
				from rest_framework.exceptions import PermissionDenied
				raise PermissionDenied("You can only view/edit settings for your own branch.")
		
		# Get or create settings
		settings, created = BranchSettings.objects.get_or_create(branch=branch)
		if created:
			settings.created_by = user
			settings.updated_by = user
			settings.save()
		
		return settings
	
	def get_serializer_class(self):
		"""Use different serializer for update."""
		if self.request.method in ['PUT', 'PATCH']:
			return BranchSettingsUpdateSerializer
		return BranchSettingsSerializer
	
	def perform_update(self, serializer):
		"""Set updated_by on settings update."""
		serializer.save(updated_by=self.request.user)
	
	@extend_schema(
		summary="Filial sozlamalarini ko'rish",
		parameters=[
			OpenApiParameter('branch_id', type=str, location=OpenApiParameter.PATH),
		],
	)
	def get(self, request, *args, **kwargs):
		return super().get(request, *args, **kwargs)
	
	@extend_schema(
		summary="Filial sozlamalarini yangilash",
		request=BranchSettingsUpdateSerializer,
		responses={200: BranchSettingsSerializer},
	)
	def patch(self, request, *args, **kwargs):
		return super().patch(request, *args, **kwargs)


# ============================================================================
# STAFF MANAGEMENT VIEWS
# ============================================================================

from rest_framework import viewsets
from rest_framework.decorators import action
from django.db.models import Q, Count, Avg
from .serializers import (
	StaffListSerializer,
	StaffDetailSerializer,
	StaffCreateSerializer,
	StaffUpdateSerializer,
	BalanceTransactionSerializer,
	SalaryPaymentSerializer,
	StaffStatsSerializer,
)
from .services import BalanceService


class StaffViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for staff management via BranchMembership model.
	
	Endpoints:
	- GET /staff/ - List all staff
	- POST /staff/ - Create new staff member
	- GET /staff/{id}/ - Get staff details
	- PATCH /staff/{id}/ - Update staff
	- DELETE /staff/{id}/ - Soft delete staff
	- GET /staff/stats/ - Get staff statistics
	- POST /staff/{id}/add_balance/ - Add balance transaction
	- POST /staff/{id}/pay_salary/ - Record salary payment
	"""
	
	queryset = BranchMembership.objects.select_related('user', 'role_ref', 'branch').all()
	permission_classes = [IsAuthenticated, HasBranchRole]
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_fields = ['branch', 'role_ref', 'employment_type']
	search_fields = ['user__first_name', 'user__last_name', 'user__phone', 'passport_serial', 'passport_number']
	ordering_fields = ['hire_date', 'monthly_salary', 'balance', 'created_at']
	ordering = ['-hire_date']
	
	def get_serializer_class(self):
		if self.action == 'create':
			return StaffCreateSerializer
		elif self.action in ['update', 'partial_update']:
			return StaffUpdateSerializer
		elif self.action == 'retrieve':
			return StaffDetailSerializer
		elif self.action == 'list':
			return StaffListSerializer
		return StaffListSerializer
	
	def get_queryset(self):
		"""Filter staff by branch access and active status.
		
		Only returns staff members (excludes students and parents).
		"""
		qs = super().get_queryset()
		
		# IMPORTANT: Exclude students and parents - only staff
		qs = qs.exclude(role__in=[BranchRole.STUDENT, BranchRole.PARENT])
		
		# Filter by branch if specified
		branch_id = self.request.query_params.get('branch')
		if branch_id:
			qs = qs.filter(branch_id=branch_id)
		
		# Filter by employment status
		status = self.request.query_params.get('status')
		if status == 'active':
			qs = qs.filter(termination_date__isnull=True)
		elif status == 'terminated':
			qs = qs.filter(termination_date__isnull=False)
		
		return qs.filter(deleted_at__isnull=True)
	
	@extend_schema(
		summary="Xodimlar ro'yxati",
		parameters=[
			OpenApiParameter('branch', type=str, description='Filial ID'),
			OpenApiParameter('role', type=str, description='Lavozim ID'),
			OpenApiParameter('employment_type', type=str, description='Ish turi'),
			OpenApiParameter('status', type=str, enum=['active', 'terminated'], description='Xodim holati'),
			OpenApiParameter('search', type=str, description='Qidiruv (ism, telefon, pasport)'),
		],
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	@extend_schema(
		summary="Yangi xodim qo'shish",
		request=StaffCreateSerializer,
		responses={201: StaffDetailSerializer},
	)
	def create(self, request, *args, **kwargs):
		return super().create(request, *args, **kwargs)
	
	@extend_schema(
		summary="Xodim to'liq ma'lumotlari",
		description="Xodimning barcha ma'lumotlari, tranzaksiyalari va to'lovlari bilan",
		responses={200: StaffDetailSerializer},
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)
	
	@extend_schema(
		summary="Xodim ma'lumotlarini yangilash",
		request=StaffUpdateSerializer,
		responses={200: StaffDetailSerializer},
	)
	def partial_update(self, request, *args, **kwargs):
		return super().partial_update(request, *args, **kwargs)
	
	@extend_schema(
		summary="Xodimni o'chirish (soft delete)",
		responses={204: None},
	)
	def destroy(self, request, *args, **kwargs):
		instance = self.get_object()
		instance.soft_delete()
		return Response(status=status.HTTP_204_NO_CONTENT)
	
	@extend_schema(
		summary="Xodimlar statistikasi",
		description="Filial bo'yicha to'liq xodimlar statistikasi",
		parameters=[
			OpenApiParameter('branch', type=str, description='Filial ID'),
		],
		responses={200: StaffStatsSerializer},
	)
	@action(detail=False, methods=['get'])
	def stats(self, request):
		"""Get comprehensive staff statistics."""
		branch_id = request.query_params.get('branch')
		qs = self.get_queryset()
		
		if branch_id:
			qs = qs.filter(branch_id=branch_id)
		
		# Basic counts
		total = qs.count()
		active = qs.filter(termination_date__isnull=True).count()
		terminated = qs.filter(termination_date__isnull=False).count()
		
		# Group by employment type (only active staff)
		by_employment_type = list(
			qs.filter(termination_date__isnull=True)
			.values('employment_type')
			.annotate(count=Count('id'))
			.order_by('-count')
		)
		
		# Group by BranchRole (basic role type)
		by_role = list(
			qs.filter(termination_date__isnull=True)
			.values('role')
			.annotate(count=Count('id'))
			.order_by('-count')
		)
		
		# Group by Role model (detailed roles)
		by_custom_role = list(
			qs.filter(termination_date__isnull=True, role_ref__isnull=False)
			.values('role_ref__id', 'role_ref__name')
			.annotate(count=Count('id'))
			.order_by('-count')
		)
		
		# Financial statistics (only active staff)
		active_qs = qs.filter(termination_date__isnull=True)
		financial_stats = active_qs.aggregate(
			avg_salary=Avg('monthly_salary'),
			total_salary_budget=models.Sum('monthly_salary'),
			total_balance=models.Sum('balance'),
			max_salary=models.Max('monthly_salary'),
			min_salary=models.Min('monthly_salary'),
		)
		
		# Payment statistics (from SalaryPayment model)
		from apps.branch.models import SalaryPayment
		from apps.branch.choices import PaymentStatus
		
		# Get all salary payments for staff members
		staff_ids = qs.values_list('id', flat=True)
		payment_stats = SalaryPayment.objects.filter(
			membership_id__in=staff_ids
		).aggregate(
			total_paid=models.Sum('amount', filter=models.Q(status=PaymentStatus.PAID)),
			total_pending=models.Sum('amount', filter=models.Q(status=PaymentStatus.PENDING)),
			paid_count=Count('id', filter=models.Q(status=PaymentStatus.PAID)),
			pending_count=Count('id', filter=models.Q(status=PaymentStatus.PENDING)),
		)
		
		data = {
			# Xodimlar soni
			'total_staff': total,
			'active_staff': active,
			'terminated_staff': terminated,
			
			# Lavozim bo'yicha
			'by_employment_type': by_employment_type,
			'by_role': by_role,
			'by_custom_role': by_custom_role,
			
			# Maosh statistikasi
			'average_salary': round(float(financial_stats['avg_salary'] or 0), 2),
			'total_salary_budget': financial_stats['total_salary_budget'] or 0,  # Oylik umumiy maosh
			'max_salary': financial_stats['max_salary'] or 0,
			'min_salary': financial_stats['min_salary'] or 0,
			
			# To'lovlar statistikasi
			'total_paid': payment_stats['total_paid'] or 0,  # Jami to'langan summa
			'total_pending': payment_stats['total_pending'] or 0,  # Kutilayotgan to'lovlar
			'paid_payments_count': payment_stats['paid_count'] or 0,  # To'langan to'lovlar soni
			'pending_payments_count': payment_stats['pending_count'] or 0,  # Kutilayotgan to'lovlar soni
			
			# Balans statistikasi
			'total_balance': financial_stats['total_balance'] or 0,  # Umumiy balans
		}
		
		serializer = StaffStatsSerializer(data)
		return Response(serializer.data)
	
	@extend_schema(
		summary="Xodim balansini o'zgartirish",
		description="""
		Admin tomonidan xodim balansini qo'lda o'zgartirish.
		
		- Balansga qo'shish: salary_accrual, bonus, advance, adjustment
		- Balansdan ayirish: deduction, fine
		- Agar create_cash_transaction=true bo'lsa, kassadan pul chiqimi ham qayd qilinadi
		- Faqat deduction va fine turlari uchun kassa tranzaksiyasi yaratiladi
		""",
		request=BalanceChangeRequestSerializer,
		responses={200: StaffDetailSerializer},
	)
	@action(detail=True, methods=['post'], url_path='change-balance')
	def change_balance(self, request, pk=None):
		"""Change staff balance with optional cash register transaction."""
		from .services import SalaryPaymentService
		from .serializers import BalanceChangeRequestSerializer
		
		staff = self.get_object()
		serializer = BalanceChangeRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			result = SalaryPaymentService.change_balance(
				staff=staff,
				transaction_type=serializer.validated_data['transaction_type'],
				amount=serializer.validated_data['amount'],
				description=serializer.validated_data['description'],
				cash_register_id=serializer.validated_data.get('cash_register_id'),
				create_cash_transaction=serializer.validated_data.get('create_cash_transaction', False),
				payment_method=serializer.validated_data.get('payment_method', 'cash'),
				reference=serializer.validated_data.get('reference', ''),
				processed_by=request.user
			)
			
			staff.refresh_from_db()
			return Response({
				'staff': StaffDetailSerializer(staff).data,
				'balance_transaction_id': str(result['balance_transaction'].id),
				'cash_transaction_id': str(result['cash_transaction'].id) if result['cash_transaction'] else None,
				'previous_balance': result['previous_balance'],
				'new_balance': result['new_balance']
			})
		
		except ValueError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
	
	@extend_schema(
		summary="Xodimga balans qo'shish",
		request=BalanceTransactionSerializer,
		responses={200: StaffDetailSerializer},
	)
	@action(detail=True, methods=['post'])
	def add_balance(self, request, pk=None):
		"""Add balance transaction to staff member."""
		from .services import BalanceService
		
		staff = self.get_object()
		serializer = BalanceTransactionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			transaction = BalanceService.apply_transaction(
				membership=staff,
				amount=serializer.validated_data['amount'],
				transaction_type=serializer.validated_data['transaction_type'],
				description=serializer.validated_data.get('description', ''),
				reference=serializer.validated_data.get('reference', ''),
				processed_by=request.user
			)
			
			staff.refresh_from_db()
			return Response(StaffDetailSerializer(staff).data)
		
		except ValueError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
	
	@extend_schema(
		summary="Oylik to'lovini qayd qilish",
		request=SalaryPaymentRequestSerializer,
		responses={200: StaffDetailSerializer},
	)
	@action(detail=True, methods=['post'])
	def pay_salary(self, request, pk=None):
		"""Process salary payment for staff member."""
		from .services import SalaryPaymentService
		from .serializers import SalaryPaymentRequestSerializer
		
		staff = self.get_object()
		serializer = SalaryPaymentRequestSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		try:
			result = SalaryPaymentService.process_salary_payment(
				staff=staff,
				amount=serializer.validated_data['amount'],
				payment_date=serializer.validated_data['payment_date'],
				payment_method=serializer.validated_data['payment_method'],
				month=serializer.validated_data['month'],
				payment_type=serializer.validated_data.get('payment_type', 'salary'),
				notes=serializer.validated_data.get('notes', ''),
				reference_number=serializer.validated_data.get('reference_number', ''),
				processed_by=request.user
			)
			
			staff.refresh_from_db()
			response_data = StaffDetailSerializer(staff).data
			response_data['payment_info'] = {
				'payment_id': str(result['payment'].id),
				'previous_balance': result['previous_balance'],
				'new_balance': result['new_balance'],
				'amount_paid': serializer.validated_data['amount']
			}
			
			return Response(response_data)
		
		except ValueError as e:
			return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
	
	@extend_schema(
		summary="Oylik maosh hisoblash",
		parameters=[
			OpenApiParameter('year', type=int, description='Yil'),
			OpenApiParameter('month', type=int, description='Oy (1-12)'),
		],
		responses={200: SalaryCalculationSerializer},
	)
	@action(detail=True, methods=['get'], url_path='calculate-salary')
	def calculate_salary(self, request, pk=None):
		"""Calculate monthly salary for staff member."""
		from .services import SalaryCalculationService
		from .serializers import SalaryCalculationSerializer
		from datetime import date
		
		staff = self.get_object()
		
		# Get year and month from query params or use current
		today = date.today()
		year = int(request.query_params.get('year', today.year))
		month = int(request.query_params.get('month', today.month))
		
		result = SalaryCalculationService.calculate_monthly_accrual(staff, year, month)
		serializer = SalaryCalculationSerializer(result)
		
		return Response(serializer.data)
	
	@extend_schema(
		summary="Oylik maosh xulosasi",
		parameters=[
			OpenApiParameter('year', type=int, description='Yil'),
			OpenApiParameter('month', type=int, description='Oy (1-12)'),
		],
		responses={200: MonthlySalarySummarySerializer},
	)
	@action(detail=True, methods=['get'], url_path='monthly-summary')
	def monthly_summary(self, request, pk=None):
		"""Get monthly salary summary for staff member."""
		from .services import SalaryPaymentService
		from .serializers import MonthlySalarySummarySerializer
		from datetime import date
		
		staff = self.get_object()
		
		# Get year and month from query params or use current
		today = date.today()
		year = int(request.query_params.get('year', today.year))
		month = int(request.query_params.get('month', today.month))
		
		summary = SalaryPaymentService.get_monthly_summary(staff, year, month)
		serializer = MonthlySalarySummarySerializer(summary)
		
		return Response(serializer.data)


class BranchSettingsViewSet(viewsets.ModelViewSet):
	"""
	ViewSet for managing branch settings.
	
	Endpoints:
	- GET /branches/settings/ - List all branch settings (superadmin only)
	- GET /branches/{branch_id}/settings/ - Get settings for specific branch
	- PATCH /branches/{branch_id}/settings/ - Update branch settings
	"""
	
	queryset = BranchSettings.objects.select_related('branch').all()
	serializer_class = BranchSettingsSerializer
	permission_classes = [IsAuthenticated, HasBranchRole]
	lookup_field = 'branch_id'
	http_method_names = ['get', 'patch', 'options', 'head']
	
	def get_queryset(self):
		"""Filter settings by user's branch access."""
		user = self.request.user
		
		# SuperAdmin can see all
		if user.is_staff or hasattr(user, 'is_superadmin') and user.is_superadmin:
			return self.queryset
		
		# BranchAdmin can see their branches
		user_branches = BranchMembership.objects.filter(
			user=user,
			role=BranchRole.BRANCH_ADMIN,
			deleted_at__isnull=True
		).values_list('branch_id', flat=True)
		
		return self.queryset.filter(branch_id__in=user_branches)
	
	@extend_schema(
		summary="Barcha filiallar sozlamalari",
		description="Barcha filiallar sozlamalarini ko'rish (faqat superadmin)",
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	@extend_schema(
		summary="Filial sozlamalari",
		description="Filialning to'liq sozlamalarini ko'rish",
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)
	
	@extend_schema(
		summary="Filial sozlamalarini yangilash",
		description="Filial sozlamalarini o'zgartirish",
		request=BranchSettingsSerializer,
		responses={200: BranchSettingsSerializer},
	)
	def partial_update(self, request, *args, **kwargs):
		return super().partial_update(request, *args, **kwargs)


class BalanceTransactionFilter(filters.FilterSet):
	"""Filter for balance transactions."""
	
	transaction_type = filters.ChoiceFilter(
		field_name='transaction_type',
		choices=[
			('salary_accrual', 'Oylik hisoblash'),
			('bonus', 'Bonus'),
			('deduction', 'Balansdan chiqarish'),
			('advance', 'Avans berish'),
			('fine', 'Jarima'),
			('adjustment', "To'g'rilash"),
			('other', 'Boshqa'),
		]
	)
	date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
	date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')
	amount_min = filters.NumberFilter(field_name='amount', lookup_expr='gte')
	amount_max = filters.NumberFilter(field_name='amount', lookup_expr='lte')
	reference = filters.CharFilter(field_name='reference', lookup_expr='icontains')
	membership = filters.UUIDFilter(field_name='membership__id')
	processed_by = filters.UUIDFilter(field_name='processed_by__id')
	
	class Meta:
		model = BalanceTransaction
		fields = ['transaction_type', 'date_from', 'date_to', 'amount_min', 'amount_max', 'reference', 'membership', 'processed_by']


class BalanceTransactionViewSet(viewsets.ReadOnlyModelViewSet):
	"""ViewSet for viewing balance transactions.
	
	Read-only endpoints for viewing transaction history with filters and search.
	Supports filtering by:
	- transaction_type: Transaction type (salary, bonus, deduction, etc.)
	- date_from/date_to: Date range filter
	- amount_min/amount_max: Amount range filter
	- reference: Search by reference number
	- membership: Filter by staff member
	- processed_by: Filter by processor
	
	Supports search by:
	- description
	- reference
	- membership user's phone number
	- membership user's full name
	
	Ordering:
	- created_at (default: descending)
	- amount
	- transaction_type
	"""
	
	queryset = BalanceTransaction.objects.select_related(
		'membership', 'membership__user', 'processed_by', 'salary_payment'
	).all()
	serializer_class = BalanceTransactionListSerializer
	permission_classes = [IsAuthenticated, HasBranchRole]
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_class = BalanceTransactionFilter
	search_fields = ['description', 'reference', 'membership__user__phone_number', 'membership__user__first_name', 'membership__user__last_name']
	ordering_fields = ['created_at', 'amount', 'transaction_type']
	ordering = ['-created_at']
	
	def get_queryset(self):
		"""Filter transactions by user's branch access."""
		user = self.request.user
		queryset = self.queryset
		
		# SuperAdmin can see all
		if user.is_staff or hasattr(user, 'is_superadmin') and user.is_superadmin:
			return queryset
		
		# BranchAdmin can see their branches
		user_branches = BranchMembership.objects.filter(
			user=user,
			role=BranchRole.BRANCH_ADMIN,
			deleted_at__isnull=True
		).values_list('branch_id', flat=True)
		
		return queryset.filter(membership__branch_id__in=user_branches)
	
	@extend_schema(
		summary="Barcha tranzaksiyalar ro'yxati",
		description="Balans tranzaksiyalari ro'yxati - filter, qidiruv va tartiblash bilan",
		parameters=[
			OpenApiParameter('transaction_type', type=str, description='Tranzaksiya turi'),
			OpenApiParameter('date_from', type=str, description='Boshlanish sanasi (YYYY-MM-DD)'),
			OpenApiParameter('date_to', type=str, description='Tugash sanasi (YYYY-MM-DD)'),
			OpenApiParameter('amount_min', type=int, description='Minimal summa'),
			OpenApiParameter('amount_max', type=int, description='Maksimal summa'),
			OpenApiParameter('reference', type=str, description='Referens raqami'),
			OpenApiParameter('membership', type=str, description='Xodim ID'),
			OpenApiParameter('processed_by', type=str, description="Kim qayd qilgan (user ID)"),
			OpenApiParameter('search', type=str, description='Qidiruv (description, reference, phone, name)'),
			OpenApiParameter('ordering', type=str, description='Tartiblash (-created_at, amount, transaction_type)'),
		],
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	@extend_schema(
		summary="Tranzaksiya tafsilotlari",
		description="Bitta tranzaksiyaning to'liq ma'lumotlari",
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)


class SalaryPaymentFilter(filters.FilterSet):
	"""Filter for salary payments."""
	
	status = filters.ChoiceFilter(
		field_name='status',
		choices=[
			('pending', 'Kutilmoqda'),
			('paid', "To'langan"),
			('cancelled', 'Bekor qilingan'),
			('failed', 'Muvaffaqiyatsiz'),
		]
	)
	payment_method = filters.ChoiceFilter(
		field_name='payment_method',
		choices=[
			('cash', 'Naqd'),
			('bank_transfer', "Bank o'tkazmasi"),
			('card', 'Karta'),
			('other', 'Boshqa'),
		]
	)
	payment_type = filters.ChoiceFilter(
		field_name='payment_type',
		choices=[
			('advance', "Avans to'lovi"),
			('salary', "Oylik to'lovi"),
			('bonus_payment', "Bonus to'lovi"),
			('other', "Boshqa to'lov"),
		]
	)
	month = filters.DateFilter(field_name='month')
	month_from = filters.DateFilter(field_name='month', lookup_expr='gte')
	month_to = filters.DateFilter(field_name='month', lookup_expr='lte')
	payment_date_from = filters.DateFilter(field_name='payment_date', lookup_expr='gte')
	payment_date_to = filters.DateFilter(field_name='payment_date', lookup_expr='lte')
	amount_min = filters.NumberFilter(field_name='amount', lookup_expr='gte')
	amount_max = filters.NumberFilter(field_name='amount', lookup_expr='lte')
	reference_number = filters.CharFilter(field_name='reference_number', lookup_expr='icontains')
	membership = filters.UUIDFilter(field_name='membership__id')
	processed_by = filters.UUIDFilter(field_name='processed_by__id')
	
	class Meta:
		model = SalaryPayment
		fields = [
			'status', 'payment_method', 'payment_type', 'month', 'month_from', 'month_to',
			'payment_date_from', 'payment_date_to', 'amount_min', 'amount_max',
			'reference_number', 'membership', 'processed_by'
		]


class SalaryPaymentViewSet(viewsets.ReadOnlyModelViewSet):
	"""ViewSet for viewing salary payments.
	
	Read-only endpoints for viewing payment history with filters and search.
	Supports filtering by:
	- status: Payment status (pending, paid, cancelled)
	- payment_method: Payment method (cash, bank_transfer, card, other)
	- payment_type: Payment type (advance, salary, bonus_payment, other)
	- month: Exact month (YYYY-MM-DD)
	- month_from/month_to: Month range filter
	- payment_date_from/payment_date_to: Payment date range
	- amount_min/amount_max: Amount range filter
	- reference_number: Search by reference number
	- membership: Filter by staff member
	- processed_by: Filter by processor
	
	Supports search by:
	- notes
	- reference_number
	- membership user's phone number
	- membership user's full name
	
	Ordering:
	- payment_date (default: descending)
	- created_at
	- amount
	- month
	"""
	
	queryset = SalaryPayment.objects.select_related(
		'membership', 'membership__user', 'processed_by'
	).prefetch_related('transactions').all()
	serializer_class = SalaryPaymentListSerializer
	permission_classes = [IsAuthenticated, HasBranchRole]
	filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
	filterset_class = SalaryPaymentFilter
	search_fields = ['notes', 'reference_number', 'membership__user__phone_number', 'membership__user__first_name', 'membership__user__last_name']
	ordering_fields = ['payment_date', 'created_at', 'amount', 'month']
	ordering = ['-payment_date', '-created_at']
	
	def get_queryset(self):
		"""Filter payments by user's branch access."""
		user = self.request.user
		queryset = self.queryset
		
		# SuperAdmin can see all
		if user.is_staff or hasattr(user, 'is_superadmin') and user.is_superadmin:
			return queryset
		
		# BranchAdmin can see their branches
		user_branches = BranchMembership.objects.filter(
			user=user,
			role=BranchRole.BRANCH_ADMIN,
			deleted_at__isnull=True
		).values_list('branch_id', flat=True)
		
		return queryset.filter(membership__branch_id__in=user_branches)
	
	@extend_schema(
		summary="Barcha to'lovlar ro'yxati",
		description="Maosh to'lovlari ro'yxati - filter, qidiruv va tartiblash bilan",
		parameters=[
			OpenApiParameter('status', type=str, description="To'lov holati (pending, paid, cancelled)"),
			OpenApiParameter('payment_method', type=str, description="To'lov usuli (cash, bank_transfer, card, other)"),
			OpenApiParameter('payment_type', type=str, description="To'lov turi (advance, salary, bonus_payment, other)"),
			OpenApiParameter('month', type=str, description='Oy (YYYY-MM-DD)'),
			OpenApiParameter('month_from', type=str, description='Oydan (YYYY-MM-DD)'),
			OpenApiParameter('month_to', type=str, description='Oygacha (YYYY-MM-DD)'),
			OpenApiParameter('payment_date_from', type=str, description="To'lov sanasidan (YYYY-MM-DD)"),
			OpenApiParameter('payment_date_to', type=str, description="To'lov sanasigacha (YYYY-MM-DD)"),
			OpenApiParameter('amount_min', type=int, description='Minimal summa'),
			OpenApiParameter('amount_max', type=int, description='Maksimal summa'),
			OpenApiParameter('reference_number', type=str, description="To'lov raqami"),
			OpenApiParameter('membership', type=str, description='Xodim ID'),
			OpenApiParameter('processed_by', type=str, description='Kim tomonidan (user ID)'),
			OpenApiParameter('search', type=str, description='Qidiruv (notes, reference, phone, name)'),
			OpenApiParameter('ordering', type=str, description='Tartiblash (-payment_date, -created_at, amount, month)'),
		],
	)
	def list(self, request, *args, **kwargs):
		return super().list(request, *args, **kwargs)
	
	@extend_schema(
		summary="To'lov tafsilotlari",
		description="Bitta to'lovning to'liq ma'lumotlari",
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)
