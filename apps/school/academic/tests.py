from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear

User = get_user_model()


class AcademicPermissionsTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active",
        )
        # Users
        self.teacher = User.objects.create_user(phone_number="+998901111111", password="testpass123")
        self.student = User.objects.create_user(phone_number="+998902222222", password="testpass123")
        self.admin = User.objects.create_user(phone_number="+998903333333", password="testpass123")
        self.super = User.objects.create_superuser(phone_number="+998904444444", password="testpass123")

        # Memberships
        BranchMembership.objects.create(user=self.teacher, branch=self.branch, role=BranchRole.TEACHER)
        BranchMembership.objects.create(user=self.student, branch=self.branch, role=BranchRole.STUDENT)
        BranchMembership.objects.create(user=self.admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)
        # super admin does not need membership

        # Sample academic year
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2024-2025",
            start_date="2024-09-01",
            end_date="2025-06-30",
            is_active=True,
        )

        self.client = APIClient()

    def test_teacher_can_read_list_but_cannot_create(self):
        self.client.force_authenticate(user=self.teacher)
        list_url = f"/api/v1/school/branches/{self.branch.id}/academic-years/"
        # GET allowed
        resp_get = self.client.get(list_url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.data)
        # POST forbidden
        payload = {
            "name": "2025-2026",
            "start_date": "2025-09-01",
            "end_date": "2026-06-30",
            "is_active": False,
        }
        resp_post = self.client.post(list_url, payload, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_read_detail_but_cannot_patch(self):
        self.client.force_authenticate(user=self.student)
        detail_url = f"/api/v1/school/branches/{self.branch.id}/academic-years/{self.academic_year.id}/"
        # GET allowed
        resp_get = self.client.get(detail_url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.data)
        # PATCH forbidden
        resp_patch = self.client.patch(detail_url, {"name": "Updated"}, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_patch.status_code, status.HTTP_403_FORBIDDEN)

    def test_branch_admin_can_patch(self):
        self.client.force_authenticate(user=self.admin)
        detail_url = f"/api/v1/school/branches/{self.branch.id}/academic-years/{self.academic_year.id}/"
        resp_patch = self.client.patch(detail_url, {"name": "Admin Updated"}, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK, resp_patch.data)
        # Verify change
        self.academic_year.refresh_from_db()
        self.assertEqual(self.academic_year.name, "Admin Updated")

    def test_super_admin_can_patch_without_membership(self):
        self.client.force_authenticate(user=self.super)
        detail_url = f"/api/v1/school/branches/{self.branch.id}/academic-years/{self.academic_year.id}/"
        resp_patch = self.client.patch(detail_url, {"name": "Super Updated"}, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)
        # Verify change
        self.academic_year.refresh_from_db()
        self.assertEqual(self.academic_year.name, "Super Updated")
