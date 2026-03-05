from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.finance.models import FinanceCategory

User = get_user_model()


class FinanceCategoryListTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.branch = Branch.objects.create(
            name="Test Branch",
            type="school",
            slug="test-branch",
            address="Test Address",
        )
        self.user = User.objects.create_user(phone_number="+998901111111", password="pass12345")
        BranchMembership.objects.create(user=self.user, branch=self.branch, role=BranchRole.BRANCH_ADMIN)

        FinanceCategory.objects.create(branch=self.branch, name="Tuition", type="income", description="Monthly fee")
        FinanceCategory.objects.create(branch=self.branch, name="Rent", type="expense", description="Office rent")

        self.client.force_authenticate(user=self.user)

    def test_list_with_search_does_not_error(self):
        url = "/api/v1/school/finance/categories/"
        response = self.client.get(
            url,
            {"search": "tui"},
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_with_legacy_ordering_code_does_not_error(self):
        url = "/api/v1/school/finance/categories/"
        response = self.client.get(
            url,
            {"ordering": "code"},
            HTTP_X_BRANCH_ID=str(self.branch.id),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
