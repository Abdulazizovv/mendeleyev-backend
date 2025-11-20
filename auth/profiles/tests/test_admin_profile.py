from __future__ import annotations

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole


User = get_user_model()


class AdminProfileTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Delta", status=BranchStatuses.ACTIVE)
        self.user_admin = User.objects.create_user(phone_number="+998900000020", password="P@ssw0rd!", phone_verified=True)
        self.user_super = User.objects.create_user(phone_number="+998900000021", password="P@ssw0rd!", phone_verified=True)
        self.user_teacher = User.objects.create_user(phone_number="+998900000022", password="P@ssw0rd!", phone_verified=True)

    def test_auto_create_admin_profile_for_branch_admin(self):
        m = BranchMembership.objects.create(user=self.user_admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)
        self.assertTrue(hasattr(m, 'generic_profile'))
        # Role-specific AdminProfile should be created
        self.assertTrue(hasattr(m, 'admin_profile'))
        self.assertFalse(m.admin_profile.is_super_admin)

    def test_auto_create_admin_profile_for_super_admin(self):
        m = BranchMembership.objects.create(user=self.user_super, branch=self.branch, role=BranchRole.SUPER_ADMIN)
        self.assertTrue(hasattr(m, 'admin_profile'))
        self.assertTrue(m.admin_profile.is_super_admin)

    def test_membership_serializer_role_data_for_admin(self):
        from auth.users.serializers import BranchMembershipSerializer
        m = BranchMembership.objects.create(user=self.user_admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)
        data = BranchMembershipSerializer.from_userbranch(m)
        # role_data should be present and include admin fields
        self.assertIn('role_data', data)
        self.assertIsInstance(data['role_data'], dict)
        self.assertIn('is_super_admin', data['role_data'])
        self.assertIn('managed_branches', data['role_data'])

    def test_role_change_teacher_to_branch_admin_creates_admin_profile(self):
        # Create as teacher first
        m = BranchMembership.objects.create(user=self.user_teacher, branch=self.branch, role=BranchRole.TEACHER)
        self.assertTrue(hasattr(m, 'teacher_profile'))
        # Change role to branch_admin and save; post_save should provision AdminProfile idempotently
        m.role = BranchRole.BRANCH_ADMIN
        m.save(update_fields=["role", "updated_at"])  # trigger post_save
        # Refresh from db
        m_ref = BranchMembership.objects.get(id=m.id)
        self.assertTrue(hasattr(m_ref, 'admin_profile'))
        # We keep previous role profiles intact (see signals TODO)
        self.assertTrue(hasattr(m_ref, 'teacher_profile'))

    def test_permission_is_branch_admin(self):
        from rest_framework.test import APIRequestFactory
        from apps.common.permissions import IsBranchAdmin
        factory = APIRequestFactory()
        m = BranchMembership.objects.create(user=self.user_admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)
        req = factory.get("/")
        req.user = self.user_admin
        req.auth = {"br": str(self.branch.id)}
        view = type("V", (), {"kwargs": {}, "required_branch_roles": ("branch_admin",)})()
        self.assertTrue(IsBranchAdmin().has_permission(req, view))
