from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear
from apps.school.classes.models import Class, ClassStudent

User = get_user_model()

class AvailableStudentsApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Test", slug="test")
        self.admin = User.objects.create_user(phone_number="+998900000010", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        BranchMembership.objects.create(user=self.admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)

        self.ay = AcademicYear.objects.create(branch=self.branch, name="2024-2025", start_date="2024-09-01", end_date="2025-06-30", is_active=True)
        self.cls = Class.objects.create(branch=self.branch, academic_year=self.ay, name="1-A", grade_level=1, max_students=30, created_by=self.admin)

        # Students
        self.u1 = User.objects.create_user(phone_number="+998900000011")
        self.u2 = User.objects.create_user(phone_number="+998900000012")
        self.u3 = User.objects.create_user(phone_number="+998900000013")
        self.m1 = BranchMembership.objects.create(user=self.u1, branch=self.branch, role=BranchRole.STUDENT)
        self.m2 = BranchMembership.objects.create(user=self.u2, branch=self.branch, role=BranchRole.STUDENT)
        self.m3 = BranchMembership.objects.create(user=self.u3, branch=self.branch, role=BranchRole.STUDENT)

        # Enroll one student
        ClassStudent.objects.create(class_obj=self.cls, membership=self.m1, created_by=self.admin)

        self.url = f"/api/v1/school/branches/{self.branch.id}/classes/{self.cls.id}/available-students/"

    def test_lists_only_not_enrolled_students(self):
        resp = self.client.get(self.url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in resp.json().get('results', [])]
        self.assertIn(str(self.m2.id), ids)
        self.assertIn(str(self.m3.id), ids)
        self.assertNotIn(str(self.m1.id), ids)

    def test_search_by_phone(self):
        resp = self.client.get(self.url + "?search=000000012", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json().get('results', [])
        self.assertTrue(any(r['user_phone'].endswith('12') for r in results))

    def test_ordering_by_name(self):
        # set names
        self.u2.first_name, self.u2.last_name = "Ali", "Bek"
        self.u3.first_name, self.u3.last_name = "Vali", "Zokirov"
        self.u2.save(); self.u3.save()
        resp = self.client.get(self.url + "?ordering=user__first_name", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [r['user_name'] for r in resp.json().get('results', [])]
        self.assertEqual(names, sorted(names))
