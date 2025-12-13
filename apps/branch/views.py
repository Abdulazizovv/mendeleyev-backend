from __future__ import annotations

from typing import Iterable

from django.shortcuts import get_object_or_404
from django.db import models
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveUpdateAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Branch, BranchStatuses, BranchMembership, Role, BranchSettings
from .serializers import (
    BranchListSerializer,
    RoleSerializer,
    RoleCreateSerializer,
    BranchMembershipDetailSerializer,
    BranchMembershipCreateSerializer,
    BalanceUpdateSerializer,
)
from .settings_serializers import (
    BranchSettingsSerializer,
    BranchSettingsUpdateSerializer,
)
from auth.users.models import User
from apps.common.permissions import HasBranchRole, IsSuperAdmin, IsBranchAdmin
from apps.common.mixins import AuditTrailMixin


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
	StaffSerializer,
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
		return StaffSerializer
	
	def get_queryset(self):
		"""Filter staff by branch access and active status."""
		qs = super().get_queryset()
		
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
		responses={201: StaffSerializer},
	)
	def create(self, request, *args, **kwargs):
		return super().create(request, *args, **kwargs)
	
	@extend_schema(
		summary="Xodim ma'lumotlari",
		responses={200: StaffSerializer},
	)
	def retrieve(self, request, *args, **kwargs):
		return super().retrieve(request, *args, **kwargs)
	
	@extend_schema(
		summary="Xodim ma'lumotlarini yangilash",
		request=StaffUpdateSerializer,
		responses={200: StaffSerializer},
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
		responses={200: StaffStatsSerializer},
	)
	@action(detail=False, methods=['get'])
	def stats(self, request):
		"""Get staff statistics."""
		branch_id = request.query_params.get('branch')
		qs = self.get_queryset()
		
		if branch_id:
			qs = qs.filter(branch_id=branch_id)
		
		total = qs.count()
		active = qs.filter(termination_date__isnull=True).count()
		terminated = qs.filter(termination_date__isnull=False).count()
		
		by_employment_type = qs.filter(termination_date__isnull=True).values(
			'employment_type'
		).annotate(count=Count('id'))
		
		by_role = qs.filter(termination_date__isnull=True).values(
			'role_ref__name'
		).annotate(count=Count('id'))
		
		avg_salary = qs.filter(termination_date__isnull=True).aggregate(
			avg=Avg('monthly_salary')
		)['avg'] or 0
		
		data = {
			'total_staff': total,
			'active_staff': active,
			'terminated_staff': terminated,
			'by_employment_type': list(by_employment_type),
			'by_role': list(by_role),
			'average_salary': round(float(avg_salary), 2),
		}
		
		serializer = StaffStatsSerializer(data)
		return Response(serializer.data)
	
	@extend_schema(
		summary="Xodimga balans qo'shish",
		request=BalanceTransactionSerializer,
		responses={200: StaffSerializer},
	)
	@action(detail=True, methods=['post'])
	def add_balance(self, request, pk=None):
		"""Add balance transaction to staff member."""
		staff = self.get_object()
		serializer = BalanceTransactionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		transaction = BalanceService.apply_transaction(
			membership=staff,
			amount=serializer.validated_data['amount'],
			transaction_type=serializer.validated_data['transaction_type'],
			description=serializer.validated_data.get('description', ''),
			created_by=request.user
		)
		
		staff.refresh_from_db()
		return Response(StaffSerializer(staff).data)
	
	@extend_schema(
		summary="Oylik to'lovini qayd qilish",
		request=SalaryPaymentSerializer,
		responses={200: StaffSerializer},
	)
	@action(detail=True, methods=['post'])
	def pay_salary(self, request, pk=None):
		"""Record salary payment for staff member."""
		staff = self.get_object()
		serializer = SalaryPaymentSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		
		from .models import SalaryPayment
		payment = SalaryPayment.objects.create(
			membership=staff,
			amount=serializer.validated_data['amount'],
			payment_method=serializer.validated_data['payment_method'],
			payment_status=serializer.validated_data.get('payment_status', 'completed'),
			notes=serializer.validated_data.get('notes', ''),
			paid_by=request.user
		)
		
		staff.refresh_from_db()
		return Response(StaffSerializer(staff).data)
