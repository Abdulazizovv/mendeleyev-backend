from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole


User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class BranchJWTTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Branches
        self.b1 = Branch.objects.create(name="Alpha", status=BranchStatuses.ACTIVE)
        self.b2 = Branch.objects.create(name="Beta", status=BranchStatuses.ACTIVE)
        self.b_arch = Branch.objects.create(name="Gamma", status=BranchStatuses.ARCHIVED)
        # Users
        self.u_single = User.objects.create_user(phone_number="+998900000001", password=None)
        self.u_single.phone_verified = True
        self.u_single.set_password("Pass123!@#")
        self.u_single.save()
        BranchMembership.objects.create(user=self.u_single, branch=self.b1, role=BranchRole.TEACHER)

        self.u_multi = User.objects.create_user(phone_number="+998900000002", password=None)
        self.u_multi.phone_verified = True
        self.u_multi.set_password("Pass123!@#")
        self.u_multi.save()
        # Multi-branch user: teacher in b1, branch_admin in b2
        BranchMembership.objects.create(user=self.u_multi, branch=self.b1, role=BranchRole.TEACHER)
        BranchMembership.objects.create(user=self.u_multi, branch=self.b2, role=BranchRole.BRANCH_ADMIN)

        self.admin = User.objects.create_user(phone_number="+998900000003", password="Admin123!@#", is_staff=True)
        self.admin.phone_verified = True
        self.admin.save()

    def login(self, phone: str, password: str, branch_id: str | None = None):
        payload = {"phone_number": phone, "password": password}
        if branch_id:
            payload["branch_id"] = str(branch_id)
        return self.client.post(reverse("auth-login"), payload, format="json")

    def test_single_branch_auto_scope(self):
        res = self.login(self.u_single.phone_number, "Pass123!@#")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        # Should include br and br_role in response
        self.assertEqual(res.data.get("br"), str(self.b1.id))
        self.assertEqual(res.data.get("br_role"), BranchRole.TEACHER)

    def test_multi_branch_requires_selection(self):
        res = self.login(self.u_multi.phone_number, "Pass123!@#")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("state"), "MULTI_BRANCH")
        self.assertTrue(isinstance(res.data.get("branches"), list))
        self.assertGreaterEqual(len(res.data.get("branches")), 2)

    def test_multi_branch_login_with_choice(self):
        res = self.login(self.u_multi.phone_number, "Pass123!@#", branch_id=self.b2.id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("br"), str(self.b2.id))
        self.assertEqual(res.data.get("br_role"), BranchRole.BRANCH_ADMIN)

    def test_admin_global_and_scoped(self):
        # Global (no branch)
        res_global = self.login(self.admin.phone_number, "Admin123!@#")
        self.assertEqual(res_global.status_code, 200)
        self.assertIn("access", res_global.data)
        self.assertNotIn("br", res_global.data)  # global token by default

        # Scoped to active branch
        res_scoped = self.login(self.admin.phone_number, "Admin123!@#", branch_id=self.b1.id)
        self.assertEqual(res_scoped.status_code, 200)
        self.assertEqual(res_scoped.data.get("br"), str(self.b1.id))

    def test_switch_branch_and_refresh_validation(self):
        # Login as multi-branch and choose b1
        res = self.login(self.u_multi.phone_number, "Pass123!@#", branch_id=self.b1.id)
        self.assertEqual(res.status_code, 200)
        refresh = res.data["refresh"]

        # Switch to b2
        sw = self.client.post(reverse("auth-branch-switch"), {"refresh": refresh, "branch_id": str(self.b2.id)}, format="json")
        self.assertEqual(sw.status_code, 200)
        self.assertEqual(sw.data.get("br"), str(self.b2.id))

        # Now try refresh token after revoking b2 membership
        # Re-login to get a refresh scoped to b2
        res_b2 = self.login(self.u_multi.phone_number, "Pass123!@#", branch_id=self.b2.id)
        self.assertEqual(res_b2.status_code, 200)
        refresh_b2 = res_b2.data["refresh"]

        # Remove membership and try refresh
        BranchMembership.objects.filter(user=self.u_multi, branch=self.b2).delete()
        rf = self.client.post(reverse("auth-refresh"), {"refresh": refresh_b2}, format="json")
        self.assertEqual(rf.status_code, 401)

        # Archived branch should be rejected on refresh
        # Give membership to archived branch and login
        BranchMembership.objects.get_or_create(user=self.u_single, branch=self.b_arch, role=BranchRole.TEACHER)
        # Can't login to archived via selection (login checks active only), but we can simulate refresh validation:
        # Issue login for active b1 first and then manipulate refresh claim via switch -> expect 400 on switch to archived
        res_active = self.login(self.u_single.phone_number, "Pass123!@#")
        self.assertEqual(res_active.status_code, 200)
        refresh_active = res_active.data["refresh"]
        sw_arch = self.client.post(reverse("auth-branch-switch"), {"refresh": refresh_active, "branch_id": str(self.b_arch.id)}, format="json")
        # Regular user cannot scope to archived branch
        self.assertEqual(sw_arch.status_code, 400)

    def test_my_branches_endpoint(self):
        # Login as multi user to get access token
        res = self.login(self.u_multi.phone_number, "Pass123!@#", branch_id=self.b1.id)
        self.assertEqual(res.status_code, 200)
        access = res.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        r = self.client.get(reverse("auth-my-branches"))
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data.get("count", 0), 2)
