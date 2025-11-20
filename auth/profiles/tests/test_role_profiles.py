from __future__ import annotations

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole

User = get_user_model()


class RoleProfilesTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Gamma", status=BranchStatuses.ACTIVE)
        self.teacher = User.objects.create_user(phone_number="+998900000010", password="P@ssw0rd!", phone_verified=True)
        self.student = User.objects.create_user(phone_number="+998900000011", password="P@ssw0rd!", phone_verified=True)
        self.parent = User.objects.create_user(phone_number="+998900000012", password="P@ssw0rd!", phone_verified=True)

    def test_auto_create_teacher_profile(self):
        m = BranchMembership.objects.create(user=self.teacher, branch=self.branch, role=BranchRole.TEACHER)
        # signals should create both generic and specific profile
        self.assertTrue(hasattr(m, 'generic_profile'))
        self.assertTrue(hasattr(m, 'teacher_profile'))

    def test_auto_create_student_profile(self):
        m = BranchMembership.objects.create(user=self.student, branch=self.branch, role=BranchRole.STUDENT)
        self.assertTrue(hasattr(m, 'generic_profile'))
        self.assertTrue(hasattr(m, 'student_profile'))

    def test_auto_create_parent_profile(self):
        m = BranchMembership.objects.create(user=self.parent, branch=self.branch, role=BranchRole.PARENT)
        self.assertTrue(hasattr(m, 'generic_profile'))
        self.assertTrue(hasattr(m, 'parent_profile'))

    def test_membership_serializer_role_data(self):
        from auth.users.serializers import BranchMembershipSerializer
        m = BranchMembership.objects.create(user=self.teacher, branch=self.branch, role=BranchRole.TEACHER)
        data = BranchMembershipSerializer.from_userbranch(m)
        self.assertIn('role_data', data)
        self.assertIsInstance(data['role_data'], dict)
        self.assertIn('subject', data['role_data'])

    def test_permission_wrappers(self):
        from rest_framework.test import APIRequestFactory
        from apps.common.permissions import IsTeacher, IsStudent, IsBranchAdmin
        factory = APIRequestFactory()
        # Create teacher membership
        m = BranchMembership.objects.create(user=self.teacher, branch=self.branch, role=BranchRole.TEACHER)
        # Fake request with JWT-like auth dict containing br claim
        req = factory.get("/")
        req.user = self.teacher
        req.auth = {"br": str(self.branch.id)}
        # Views with required roles
        view = type("V", (), {"kwargs": {}, "required_branch_roles": ("teacher",)})()
        self.assertTrue(IsTeacher().has_permission(req, view))
        self.assertFalse(IsStudent().has_permission(req, view))
        self.assertFalse(IsBranchAdmin().has_permission(req, view))
