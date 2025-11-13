from __future__ import annotations

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.branch.models import Branch, BranchStatuses, BranchMembership
from apps.branch.views import ManagedBranchesView
from auth.users.models import BranchRole

User = get_user_model()


class ManagedBranchesTests(TestCase):
    def setUp(self):
        # Branches
        self.b1 = Branch.objects.create(name="Downtown Campus", status=BranchStatuses.ACTIVE)
        self.b2 = Branch.objects.create(name="North Campus", status=BranchStatuses.ACTIVE)
        self.b3 = Branch.objects.create(name="East Campus", status=BranchStatuses.INACTIVE)
        # Users
        self.u_super = User.objects.create_user(phone_number="+998900000030", password="P@ssw0rd!", phone_verified=True)
        self.u_admin = User.objects.create_user(phone_number="+998900000031", password="P@ssw0rd!", phone_verified=True)
        self.u_student = User.objects.create_user(phone_number="+998900000032", password="P@ssw0rd!", phone_verified=True)
        # Memberships
        BranchMembership.objects.create(user=self.u_super, branch=self.b1, role=BranchRole.SUPER_ADMIN)
        BranchMembership.objects.create(user=self.u_admin, branch=self.b1, role=BranchRole.BRANCH_ADMIN)
        BranchMembership.objects.create(user=self.u_student, branch=self.b2, role=BranchRole.STUDENT)

        self.factory = APIRequestFactory()
        self.view = ManagedBranchesView.as_view()

    def test_super_admin_gets_all_active(self):
        req = self.factory.get("/api/branches/managed/")
        req.user = self.u_super
        force_authenticate(req, user=self.u_super)
        res = self.view(req)
        self.assertEqual(res.status_code, 200)
        names = [b["name"] for b in res.data]
        self.assertIn("Downtown Campus", names)
        self.assertIn("North Campus", names)
        # inactive should not be included
        self.assertNotIn("East Campus", names)

    def test_branch_admin_gets_own_membership_branches(self):
        # Admin currently is member of b1 only
        req = self.factory.get("/api/branches/managed/")
        req.user = self.u_admin
        force_authenticate(req, user=self.u_admin)
        res = self.view(req)
        self.assertEqual(res.status_code, 200)
        ids = [b["id"] for b in res.data]
        self.assertEqual(set(ids), {str(self.b1.id)})

    def test_student_forbidden(self):
        req = self.factory.get("/api/branches/managed/")
        req.user = self.u_student
        force_authenticate(req, user=self.u_student)
        res = self.view(req)
        self.assertEqual(res.status_code, 403)

    def test_super_admin_patch_updates_managed(self):
        # Create admin membership for target user on b2 as well to ensure AdminProfile anchor exists
        BranchMembership.objects.create(user=self.u_admin, branch=self.b2, role=BranchRole.BRANCH_ADMIN)
        payload = {
            "user_id": str(self.u_admin.id),
            "branch_ids": [str(self.b1.id), str(self.b2.id)],
        }
        req = self.factory.patch("/api/branches/managed/", data=payload, format="json")
        force_authenticate(req, user=self.u_super)
        res = self.view(req)
        self.assertEqual(res.status_code, 200)
        # Verify AdminProfile managed_branches assigned on first admin membership
        m = BranchMembership.objects.filter(user=self.u_admin, role='branch_admin').first()
        ap = getattr(m, 'admin_profile', None)
        self.assertIsNotNone(ap)
        managed_ids = set(ap.managed_branches.values_list('id', flat=True))
        self.assertEqual(managed_ids, {self.b1.id, self.b2.id})
