from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear, Quarter
from apps.school.classes.models import Class
from apps.school.subjects.models import Subject, ClassSubject

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
    
    def test_create_subject(self):
        """Fan yaratish testi."""
        subject = Subject.objects.create(
            branch=self.branch,
            name="Matematika",
            code="MATH",
            description="Matematika fani",
            created_by=self.user
        )
        self.assertEqual(subject.name, "Matematika")
        self.assertEqual(subject.code, "MATH")
        self.assertTrue(subject.is_active)


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

