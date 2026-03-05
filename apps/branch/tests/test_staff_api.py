from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.branch.models import Branch, BranchMembership, BranchRole

User = get_user_model()


class StaffCreateApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Main", slug="main")
        self.admin = User.objects.create_user(phone_number="+998900000010", password="pass")
        BranchMembership.objects.create(user=self.admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)

        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.url = "/api/v1/branches/staff/"

    def test_create_staff_returns_detail_serializer(self):
        payload = {
            "phone_number": "+998900000011",
            "first_name": "Ali",
            "last_name": "Xodim",
            "branch_id": str(self.branch.id),
            "role": BranchRole.TEACHER,
            "monthly_salary": 1000000,
        }
        resp = self.client.post(self.url, payload, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertEqual(data["phone_number"], payload["phone_number"])
        self.assertIn("id", data)

        # Search should not error (regression for invalid `user__phone` search field)
        search_resp = self.client.get(
            self.url,
            {"search": "0000011"},
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)
