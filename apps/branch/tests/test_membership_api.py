from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, BranchRole

User = get_user_model()

class MembershipApiFilterSearchOrderingTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Main", slug="main")
        self.admin = User.objects.create_user(phone_number="+998900000001", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        # Admin membership for branch
        BranchMembership.objects.create(user=self.admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)
        # Create sample users and memberships
        self.u_teacher = User.objects.create_user(phone_number="+998900000002", first_name="Ali", last_name="Usta")
        self.u_student = User.objects.create_user(phone_number="+998900000003", first_name="Vali", last_name="Oquvchi")
        self.u_other = User.objects.create_user(phone_number="+998900000004", first_name="Karim", last_name="Buxgalter")

        self.m_teacher = BranchMembership.objects.create(user=self.u_teacher, branch=self.branch, role=BranchRole.TEACHER, title="Fizika")
        self.m_student = BranchMembership.objects.create(user=self.u_student, branch=self.branch, role=BranchRole.STUDENT, title="9-sinf")
        self.m_other = BranchMembership.objects.create(user=self.u_other, branch=self.branch, role=BranchRole.OTHER, title="Buxgalter", balance=500000)

        self.url = f"/api/v1/branches/{self.branch.id}/memberships/"

    def test_filter_by_role(self):
        resp = self.client.get(self.url + "?role=teacher", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        roles = [item['role'] for item in resp.json().get('results', [])]
        self.assertTrue(all(r == BranchRole.TEACHER for r in roles))

    def test_search_by_user_name(self):
        resp = self.client.get(self.url + "?search=Ali", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [item.get('user_name') for item in resp.json().get('results', [])]
        self.assertIn("Ali Usta", names)

    def test_ordering_by_balance_desc(self):
        resp = self.client.get(self.url + "?ordering=-balance", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json().get('results', [])
        balances = [item.get('balance', 0) for item in results]
        self.assertEqual(balances, sorted(balances, reverse=True))
