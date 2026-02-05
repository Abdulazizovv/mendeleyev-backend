from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchStatuses, BranchMembership


User = get_user_model()


class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_me_view_with_branch_context(self):
        user = User.objects.create_user(phone_number="+998901112233", password="Passw0rd!", first_name="John")
        branch = Branch.objects.create(name="Chilonzor Branch", status=BranchStatuses.ACTIVE)
        BranchMembership.objects.create(user=user, branch=branch, role="teacher", title="Math Teacher")

        self.client.force_authenticate(user=user, token={"br": str(branch.id), "br_role": "teacher"})
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in ["user", "profile", "current_branch", "memberships", "auth_state"]:
            self.assertIn(key, data)
        self.assertEqual(data["auth_state"], user.auth_state)
        current = data["current_branch"]
        self.assertIsNotNone(current)
        self.assertEqual(current["branch_id"], str(branch.id))
        self.assertEqual(current["role"], "teacher")
        self.assertTrue(any(m["branch_id"] == str(branch.id) for m in data["memberships"]))

    def test_me_view_without_branch_scope(self):
        user = User.objects.create_user(phone_number="+998909998877", password="Passw0rd!", first_name="Alice")
        self.client.force_authenticate(user=user)
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data["current_branch"])
        self.assertEqual(data["memberships"], [])

    def test_me_view_auto_select_single_branch(self):
        """Test that when user has only one branch membership and no branch scope in token,
        the single branch should be automatically selected as current_branch"""
        user = User.objects.create_user(phone_number="+998907778899", password="Passw0rd!", first_name="Bob")
        branch = Branch.objects.create(name="Qo'qon Branch", status=BranchStatuses.ACTIVE)
        BranchMembership.objects.create(user=user, branch=branch, role="branch_admin", title="")

        # Authenticate without branch scope in token
        self.client.force_authenticate(user=user)
        resp = self.client.get("/api/v1/auth/me/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        # Verify current_branch is automatically set
        self.assertIsNotNone(data["current_branch"])
        self.assertEqual(data["current_branch"]["branch_id"], str(branch.id))
        self.assertEqual(data["current_branch"]["branch_name"], "Qo'qon Branch")
        self.assertEqual(data["current_branch"]["role"], "branch_admin")
        
        # Verify memberships also contain the same branch
        self.assertEqual(len(data["memberships"]), 1)
        self.assertEqual(data["memberships"][0]["branch_id"], str(branch.id))
