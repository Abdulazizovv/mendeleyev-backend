from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear, Quarter
from apps.school.classes.models import Class, ClassStudent
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.rooms.models import Building, Room

User = get_user_model()


class ClassModelTests(TestCase):
    """Class model testlari."""
    
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
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
        self.teacher_membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER,
            title="Math Teacher"
        )
    
    def test_create_class(self):
        """Sinf yaratish testi."""
        class_obj = Class.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="1-A",
            grade_level=1,
            section="A",
            class_teacher=self.teacher_membership,
            max_students=30,
            created_by=self.user
        )
        self.assertEqual(class_obj.name, "1-A")
        self.assertEqual(class_obj.grade_level, 1)
        self.assertEqual(class_obj.current_students_count, 0)
        self.assertTrue(class_obj.can_add_student())
    
    def test_current_students_count(self):
        """Joriy o'quvchilar soni testi."""
        class_obj = Class.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="1-A",
            grade_level=1,
            max_students=30,
            created_by=self.user
        )
        
        # O'quvchi yaratish
        student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123"
        )
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        
        # O'quvchini sinfga qo'shish
        ClassStudent.objects.create(
            class_obj=class_obj,
            membership=student_membership,
            created_by=self.user
        )
        
        self.assertEqual(class_obj.current_students_count, 1)
        self.assertTrue(class_obj.can_add_student())
        
        # Maksimal o'quvchilar soniga yetganda
        class_obj.max_students = 1
        class_obj.save()
        self.assertFalse(class_obj.can_add_student())


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


class RoomModelTests(TestCase):
    """Room model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.building = Building.objects.create(
            branch=self.branch,
            name="Asosiy bino",
            floors=3
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
    
    def test_create_room(self):
        """Xona yaratish testi."""
        room = Room.objects.create(
            branch=self.branch,
            building=self.building,
            name="101",
            room_type="classroom",
            floor=1,
            capacity=30,
            created_by=self.user
        )
        self.assertEqual(room.name, "101")
        self.assertEqual(room.room_type, "classroom")
        self.assertEqual(room.floor, 1)
        self.assertEqual(room.capacity, 30)
    
    def test_room_floor_validation(self):
        """Xona qavat validatsiyasi testi."""
        # Qavat binoning qavatlar sonidan oshib ketmasligi kerak
        with self.assertRaises(ValueError):
            Room.objects.create(
                branch=self.branch,
                building=self.building,
                name="401",
                room_type="classroom",
                floor=4,  # Bino faqat 3 qavatli
                capacity=30,
                created_by=self.user
            )

