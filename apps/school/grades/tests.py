from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear, Quarter
from apps.school.classes.models import Class
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.grades.models import AssessmentType, Assessment, Grade, QuarterGrade
from auth.profiles.models import TeacherProfile, StudentProfile

User = get_user_model()


class AssessmentTypeModelTest(TestCase):
    """Test AssessmentType model and constraints."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
    
    def test_create_assessment_type(self):
        """Test creating assessment type."""
        atype = AssessmentType.objects.create(
            branch=self.branch,
            name="Quiz",
            code="quiz",
            default_max_score=Decimal("10.00"),
            default_weight=Decimal("0.20")
        )
        self.assertEqual(atype.name, "Quiz")
        self.assertEqual(atype.default_weight, Decimal("0.20"))
    
    def test_unique_code_per_branch(self):
        """Test code uniqueness per branch."""
        AssessmentType.objects.create(
            branch=self.branch,
            name="Quiz",
            code="quiz",
            default_max_score=Decimal("10.00"),
            default_weight=Decimal("0.20")
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            AssessmentType.objects.create(
                branch=self.branch,
                name="Quiz 2",
                code="quiz",  # Duplicate code
                default_max_score=Decimal("10.00"),
                default_weight=Decimal("0.20")
            )


class GradeModelTest(TestCase):
    """Test Grade model with automatic + manual calculation."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch, name="2025-2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 6, 30)
        )
        self.quarter = Quarter.objects.create(
            academic_year=self.academic_year, name="Q1", number=1,
            start_date=date(2025, 9, 1), end_date=date(2025, 11, 30)
        )
        self.class_obj = Class.objects.create(
            branch=self.branch, name="5A", grade_level=5, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        
        teacher_user = User.objects.create_user(phone_number="+998900000001")
        teacher_membership = BranchMembership.objects.create(
            user=teacher_user, branch=self.branch, role=BranchRole.TEACHER
        )
        teacher = TeacherProfile.objects.create(user_branch=teacher_membership)
        
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj, subject=self.subject, teacher=teacher
        )
        
        student_user = User.objects.create_user(phone_number="+998900000002")
        student_membership = BranchMembership.objects.create(
            user=student_user, branch=self.branch, role=BranchRole.STUDENT
        )
        self.student = StudentProfile.objects.create(user_branch=student_membership)
        
        self.atype = AssessmentType.objects.create(
            branch=self.branch, name="Exam", code="exam",
            default_max_score=Decimal("5.00"), default_weight=Decimal("1.00")
        )
        
        self.assessment = Assessment.objects.create(
            class_subject=self.class_subject,
            assessment_type=self.atype,
            quarter=self.quarter,
            title="Midterm",
            date=date.today(),
            max_score=Decimal("100.00"),
            weight=Decimal("0.40")
        )
    
    def test_auto_calculate_score(self):
        """Test automatic score calculation (percentage)."""
        grade = Grade.objects.create(
            assessment=self.assessment,
            student=self.student,
            score=Decimal("80.00")  # 80/100 = 80%
        )
        
        # Calculated score should be auto-set
        self.assertEqual(grade.calculated_score, Decimal("4.00"))  # 80% of 5 = 4.0
    
    def test_manual_override_requires_reason(self):
        """Test manual override validation."""
        grade = Grade.objects.create(
            assessment=self.assessment,
            student=self.student,
            score=Decimal("80.00")
        )
        
        # Setting final_score without reason should fail validation
        grade.final_score = Decimal("5.00")
        
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            grade.full_clean()


class QuarterGradeCalculationTest(TestCase):
    """Test weighted average calculation for quarter grades."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch, name="2025-2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 6, 30)
        )
        self.quarter = Quarter.objects.create(
            academic_year=self.academic_year, name="Q1", number=1,
            start_date=date(2025, 9, 1), end_date=date(2025, 11, 30)
        )
        self.class_obj = Class.objects.create(
            branch=self.branch, name="5A", grade_level=5, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        
        teacher_user = User.objects.create_user(phone_number="+998900000001")
        teacher_membership = BranchMembership.objects.create(
            user=teacher_user, branch=self.branch, role=BranchRole.TEACHER
        )
        teacher = TeacherProfile.objects.create(user_branch=teacher_membership)
        
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj, subject=self.subject, teacher=teacher
        )
        
        student_user = User.objects.create_user(phone_number="+998900000002")
        student_membership = BranchMembership.objects.create(
            user=student_user, branch=self.branch, role=BranchRole.STUDENT
        )
        self.student = StudentProfile.objects.create(user_branch=student_membership)
    
    def test_weighted_average(self):
        """Test weighted average calculation."""
        # Create assessment types
        quiz_type = AssessmentType.objects.create(
            branch=self.branch, name="Quiz", code="quiz",
            default_max_score=Decimal("5.00"), default_weight=Decimal("0.30")
        )
        exam_type = AssessmentType.objects.create(
            branch=self.branch, name="Exam", code="exam",
            default_max_score=Decimal("5.00"), default_weight=Decimal("0.70")
        )
        
        # Create assessments
        quiz = Assessment.objects.create(
            class_subject=self.class_subject, assessment_type=quiz_type,
            quarter=self.quarter, title="Quiz 1", date=date.today(),
            max_score=Decimal("100.00"), weight=Decimal("0.30")
        )
        exam = Assessment.objects.create(
            class_subject=self.class_subject, assessment_type=exam_type,
            quarter=self.quarter, title="Midterm", date=date.today(),
            max_score=Decimal("100.00"), weight=Decimal("0.70")
        )
        
        # Create grades: Quiz = 5.0, Exam = 4.0
        Grade.objects.create(
            assessment=quiz, student=self.student,
            score=Decimal("100.00")  # 100% = 5.0
        )
        Grade.objects.create(
            assessment=exam, student=self.student,
            score=Decimal("80.00")  # 80% = 4.0
        )
        
        # Calculate quarter grade
        qgrade = QuarterGrade.objects.create(
            student=self.student,
            class_subject=self.class_subject,
            quarter=self.quarter,
            calculated_grade=Decimal("0.00")
        )
        qgrade.calculate()
        qgrade.refresh_from_db()
        
        # Expected: (5.0 * 0.30) + (4.0 * 0.70) = 1.5 + 2.8 = 4.30
        self.assertEqual(qgrade.calculated_grade, Decimal("4.30"))


class GradeLockingTest(TestCase):
    """Test assessment locking functionality."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch, name="2025-2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 6, 30)
        )
        self.quarter = Quarter.objects.create(
            academic_year=self.academic_year, name="Q1", number=1,
            start_date=date(2025, 9, 1), end_date=date(2025, 11, 30)
        )
        self.class_obj = Class.objects.create(
            branch=self.branch, name="5A", grade_level=5, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        
        teacher_user = User.objects.create_user(phone_number="+998900000001")
        teacher_membership = BranchMembership.objects.create(
            user=teacher_user, branch=self.branch, role=BranchRole.TEACHER
        )
        teacher = TeacherProfile.objects.create(user_branch=teacher_membership)
        
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj, subject=self.subject, teacher=teacher
        )
        
        atype = AssessmentType.objects.create(
            branch=self.branch, name="Exam", code="exam",
            default_max_score=Decimal("5.00"), default_weight=Decimal("1.00")
        )
        
        self.assessment = Assessment.objects.create(
            class_subject=self.class_subject, assessment_type=atype,
            quarter=self.quarter, title="Midterm", date=date.today(),
            max_score=Decimal("100.00")
        )
    
    def test_lock_assessment(self):
        """Test locking an assessment."""
        self.assertFalse(self.assessment.is_locked)
        
        self.assessment.lock()
        self.assessment.refresh_from_db()
        
        self.assertTrue(self.assessment.is_locked)
        self.assertIsNotNone(self.assessment.locked_at)
    
    def test_unlock_assessment(self):
        """Test unlocking (admin override)."""
        self.assessment.lock()
        self.assessment.unlock()
        self.assessment.refresh_from_db()
        
        self.assertFalse(self.assessment.is_locked)
        self.assertIsNone(self.assessment.locked_at)
