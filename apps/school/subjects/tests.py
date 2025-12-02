from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear, Quarter
from apps.school.classes.models import Class
from apps.school.subjects.models import Subject, ClassSubject
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class SubjectModelTests(TestCase):
    """Subject model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_subject(self):
        """Fan yaratish testi."""
        subject = Subject.objects.create(
            branch=self.branch,
            name="Matematika",
            code="MATH",
            description="Matematika fani",
            color="#2D9CDB",
            created_by=self.user
        )
        self.assertEqual(subject.name, "Matematika")
        self.assertEqual(subject.code, "MATH")
        self.assertEqual(subject.color, "#2D9CDB")
        self.assertTrue(subject.is_active)

    def test_subject_color_validation(self):
        """Rang HEX formatda bo'lishi kerak."""
        subject = Subject(
            branch=self.branch,
            name="Fizika",
            code="PHYS",
            color="#XYZXYZ",
            created_by=self.user
        )
        with self.assertRaises(ValidationError):
            subject.full_clean()

    def test_subject_detail_serializer_fields(self):
        """Subject detail should include stats fields and color."""
        subject = Subject.objects.create(
            branch=self.branch,
            name="Biologiya",
            code="BIO",
            color="#27AE60",
            created_by=self.user
        )
        # Add a class and teacher assignment to populate stats
        from apps.school.academic.models import AcademicYear
        from apps.school.classes.models import Class
        ay = AcademicYear.objects.create(
            branch=self.branch,
            name="2024-2025",
            start_date="2024-09-01",
            end_date="2025-06-30",
            is_active=True
        )
        class_obj = Class.objects.create(
            branch=self.branch,
            academic_year=ay,
            name="2-A",
            grade_level=2,
            max_students=30,
            created_by=self.user
        )
        teacher_user = User.objects.create_user(
            phone_number="+998901234580",
            password="testpass123",
            first_name="Teacher",
            last_name="Bio"
        )
        teacher_membership = BranchMembership.objects.create(
            user=teacher_user,
            branch=self.branch,
            role=BranchRole.TEACHER
        )
        ClassSubject.objects.create(
            class_obj=class_obj,
            subject=subject,
            teacher=teacher_membership,
            hours_per_week=3,
            created_by=self.user
        )
        from apps.school.subjects.serializers import SubjectDetailSerializer
        ser = SubjectDetailSerializer(subject)
        self.assertIn('color', ser.data)
        self.assertEqual(ser.data['color'], '#27AE60')
        self.assertEqual(ser.data['total_classes'], 1)
        self.assertEqual(ser.data['active_classes'], 1)
        self.assertEqual(len(ser.data['teachers']), 1)
        self.assertEqual(len(ser.data['class_subjects']), 1)

    def test_soft_delete_subject(self):
        """Deleting a subject should soft-delete (set deleted_at) and exclude from active queryset."""
        subject = Subject.objects.create(
            branch=self.branch,
            name="Kimyo",
            code="CHEM",
            created_by=self.user
        )
        self.assertIsNone(subject.deleted_at)
        subject.delete()
        subject.refresh_from_db()
        self.assertIsNotNone(subject.deleted_at)
        # Active filter should exclude it
        self.assertFalse(Subject.objects.filter(id=subject.id, deleted_at__isnull=True).exists())

    def test_subject_delete_api_soft(self):
        """DELETE endpoint should soft-delete and return 204, then 404 on subsequent GET."""
        subject = Subject.objects.create(
            branch=self.branch,
            name="Geometriya",
            code="GEOM",
            created_by=self.user
        )
        url = f"/api/v1/school/branches/{self.branch.id}/subjects/{subject.id}/"
        # Emulate branch role membership (user must have a BranchMembership)
        BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
        )
        resp_get = self.client.get(url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_get.status_code, status.HTTP_200_OK, resp_get.data)
        # Delete
        resp_del = self.client.delete(url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_del.status_code, status.HTTP_204_NO_CONTENT)
        # Fetch again should 404
        resp_get2 = self.client.get(url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(resp_get2.status_code, status.HTTP_404_NOT_FOUND)
        # DB row still exists with deleted_at set
        subject.refresh_from_db()
        self.assertIsNotNone(subject.deleted_at)

    def test_subject_delete_not_in_list(self):
        """Fanni o'chirgandan keyin ro'yxatda ko'rinmasligi kerak."""
        subject = Subject.objects.create(
            branch=self.branch,
            name="Tarix",
            code="HIST",
            created_by=self.user
        )

        list_url = f"/api/v1/school/branches/{self.branch.id}/subjects/"
        # Oldindan ro'yxatda bor
        BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
        )
        list_resp_before = self.client.get(list_url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(list_resp_before.status_code, 200)
        self.assertTrue(any(item['id'] == str(subject.id) for item in list_resp_before.json().get('results', [])))

        # Delete
        detail_url = f"/api/v1/school/branches/{self.branch.id}/subjects/{subject.id}/"
        del_resp = self.client.delete(detail_url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(del_resp.status_code, 204)
        subject.refresh_from_db()
        self.assertIsNotNone(subject.deleted_at)

        # Ro'yxatdan yo'q bo'lishi kerak
        list_resp_after = self.client.get(list_url, HTTP_X_BRANCH_ID=str(self.branch.id))
        self.assertEqual(list_resp_after.status_code, 200)
        self.assertFalse(any(item['id'] == str(subject.id) for item in list_resp_after.json().get('results', [])))

class ClassSubjectModelTests(TestCase):
    """ClassSubject model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2024-2025",
            start_date="2024-09-01",
            end_date="2025-06-30",
            is_active=True
        )
        self.quarter = Quarter.objects.create(
            academic_year=self.academic_year,
            name="1-chorak",
            number=1,
            start_date="2024-09-01",
            end_date="2024-11-30",
            is_active=True
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
        self.teacher_membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER
        )
        self.class_obj = Class.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="1-A",
            grade_level=1,
            max_students=30,
            created_by=self.user
        )
        self.subject = Subject.objects.create(
            branch=self.branch,
            name="Matematika",
            code="MATH",
            created_by=self.user
        )
    
    def test_create_class_subject(self):
        """Sinfga fan qo'shish testi."""
        class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj,
            subject=self.subject,
            teacher=self.teacher_membership,
            hours_per_week=4,
            quarter=self.quarter,
            created_by=self.user
        )
        self.assertEqual(class_subject.class_obj, self.class_obj)
        self.assertEqual(class_subject.subject, self.subject)
        self.assertEqual(class_subject.teacher, self.teacher_membership)
        self.assertEqual(class_subject.hours_per_week, 4)
    
    def test_class_subject_validation(self):
        """Sinf fani validatsiyasi testi."""
        # Boshqa filialga tegishli fan qo'shishga urinish
        other_branch = Branch.objects.create(
            name="Other School",
            slug="other-school",
            type="school",
            status="active"
        )
        other_subject = Subject.objects.create(
            branch=other_branch,
            name="Fizika",
            code="PHYS",
            created_by=self.user
        )
        
        with self.assertRaises(ValueError):
            ClassSubject.objects.create(
                class_obj=self.class_obj,
                subject=other_subject,
                teacher=self.teacher_membership,
                hours_per_week=4,
                created_by=self.user
            )

