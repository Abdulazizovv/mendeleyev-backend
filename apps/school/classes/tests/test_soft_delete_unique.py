from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear
from apps.school.classes.models import Class, ClassStudent

User = get_user_model()


class SoftDeleteUniqueConstraintTests(TestCase):
    """Test that unique constraints work correctly with soft delete."""

    def setUp(self):
        self.branch = Branch.objects.create(name="Test", slug="test")
        self.admin = User.objects.create_user(phone_number="+998900000010", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        BranchMembership.objects.create(user=self.admin, branch=self.branch, role=BranchRole.BRANCH_ADMIN)

        self.ay = AcademicYear.objects.create(
            branch=self.branch,
            name="2024-2025",
            start_date="2024-09-01",
            end_date="2025-06-30",
            is_active=True
        )

    def test_can_recreate_class_after_soft_delete(self):
        """Sinf yaratib, soft delete qilib, yana o'sha nomdagi sinfni yaratish mumkin bo'lishi kerak."""
        # Create class
        cls = Class.objects.create(
            branch=self.branch,
            academic_year=self.ay,
            name="1-A",
            grade_level=1,
            max_students=30,
            created_by=self.admin
        )
        self.assertIsNotNone(cls.id)
        self.assertIsNone(cls.deleted_at)

        # Soft delete
        cls.delete()
        cls.refresh_from_db()
        self.assertIsNotNone(cls.deleted_at)

        # Create new class with same name - should succeed
        cls2 = Class.objects.create(
            branch=self.branch,
            academic_year=self.ay,
            name="1-A",
            grade_level=1,
            max_students=30,
            created_by=self.admin
        )
        self.assertIsNotNone(cls2.id)
        self.assertIsNone(cls2.deleted_at)
        self.assertNotEqual(cls.id, cls2.id)

    def test_can_recreate_class_via_api_after_delete(self):
        """API orqali sinf yaratib, o'chirib, qayta yaratish mumkin bo'lishi kerak."""
        url = f"/api/v1/school/branches/{self.branch.id}/classes/"
        payload = {
            "branch": str(self.branch.id),
            "academic_year": str(self.ay.id),
            "name": "2-B",
            "grade_level": 2,
            "max_students": 25,
            "is_active": True
        }

        # Create
        resp1 = self.client.post(url, payload, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED, resp1.json())
        class_id = resp1.json()['id']

        # Delete
        delete_url = f"/api/v1/school/branches/{self.branch.id}/classes/{class_id}/"
        resp_del = self.client.delete(delete_url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_del.status_code, status.HTTP_204_NO_CONTENT)

        # Recreate with same name - should succeed
        resp2 = self.client.post(url, payload, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED, resp2.json())
        self.assertNotEqual(resp2.json()['id'], class_id)

    def test_can_re_enroll_student_after_soft_delete(self):
        """O'quvchini sinfga qo'shib, o'chirib, qayta qo'shish mumkin bo'lishi kerak."""
        cls = Class.objects.create(
            branch=self.branch,
            academic_year=self.ay,
            name="3-A",
            grade_level=3,
            max_students=30,
            created_by=self.admin
        )
        student_user = User.objects.create_user(phone_number="+998900000011")
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )

        # Enroll
        cs = ClassStudent.objects.create(
            class_obj=cls,
            membership=student_membership,
            created_by=self.admin
        )
        self.assertIsNone(cs.deleted_at)

        # Soft delete enrollment
        cs.delete()
        cs.refresh_from_db()
        self.assertIsNotNone(cs.deleted_at)

        # Re-enroll - should succeed
        cs2 = ClassStudent.objects.create(
            class_obj=cls,
            membership=student_membership,
            created_by=self.admin
        )
        self.assertIsNotNone(cs2.id)
        self.assertIsNone(cs2.deleted_at)
        self.assertNotEqual(cs.id, cs2.id)

    def test_cannot_create_duplicate_active_class(self):
        """Faol sinf uchun duplicate yaratish mumkin bo'lmasligi kerak."""
        Class.objects.create(
            branch=self.branch,
            academic_year=self.ay,
            name="4-C",
            grade_level=4,
            max_students=30,
            created_by=self.admin
        )

        # Try to create duplicate - should fail
        with self.assertRaises(Exception):  # IntegrityError
            Class.objects.create(
                branch=self.branch,
                academic_year=self.ay,
                name="4-C",
                grade_level=4,
                max_students=30,
                created_by=self.admin
            )
