from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear
from apps.school.classes.models import Class, ClassStudent
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.homework.models import (
    Homework, HomeworkSubmission, HomeworkStatus, SubmissionStatus
)
from auth.profiles.models import TeacherProfile, StudentProfile

User = get_user_model()


class HomeworkModelTest(TestCase):
    """Test Homework model validation."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch, name="2025-2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 6, 30)
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
    
    def test_create_homework(self):
        """Test basic homework creation."""
        homework = Homework.objects.create(
            class_subject=self.class_subject,
            title="Chapter 1 Exercises",
            description="Complete exercises 1-10",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
        self.assertEqual(homework.status, HomeworkStatus.ACTIVE)
        self.assertTrue(homework.allow_late_submission)
    
    def test_due_date_validation(self):
        """Test due_date must be >= assigned_date."""
        from django.core.exceptions import ValidationError
        
        homework = Homework(
            class_subject=self.class_subject,
            title="Test",
            description="Test",
            assigned_date=date.today(),
            due_date=date.today() - timedelta(days=1)  # Invalid: before assigned_date
        )
        
        with self.assertRaises(ValidationError):
            homework.full_clean()
    
    def test_is_overdue(self):
        """Test overdue detection."""
        homework = Homework.objects.create(
            class_subject=self.class_subject,
            title="Test",
            description="Test",
            assigned_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=1)
        )
        self.assertTrue(homework.is_overdue())


class HomeworkSubmissionTest(TestCase):
    """Test HomeworkSubmission model and status transitions."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch, name="2025-2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 6, 30)
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
        
        ClassStudent.objects.create(
            class_obj=self.class_obj,
            membership=student_membership,
            is_active=True
        )
        
        self.homework = Homework.objects.create(
            class_subject=self.class_subject,
            title="Test Homework",
            description="Test",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
    
    def test_create_submission(self):
        """Test creating submission."""
        submission = HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            submission_text="My answer"
        )
        self.assertEqual(submission.status, SubmissionStatus.NOT_SUBMITTED)
        self.assertFalse(submission.is_late)
    
    def test_submit_on_time(self):
        """Test submitting before due date."""
        submission = HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            submission_text="My answer"
        )
        
        submission.submit()
        submission.refresh_from_db()
        
        self.assertEqual(submission.status, SubmissionStatus.SUBMITTED)
        self.assertFalse(submission.is_late)
        self.assertIsNotNone(submission.submitted_at)
    
    def test_late_submission_detection(self):
        """Test automatic late detection."""
        # Create homework with past due date
        past_homework = Homework.objects.create(
            class_subject=self.class_subject,
            title="Past Homework",
            description="Test",
            assigned_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=1),
            allow_late_submission=True
        )
        
        submission = HomeworkSubmission.objects.create(
            homework=past_homework,
            student=self.student,
            submission_text="Late answer"
        )
        
        submission.submit()
        submission.refresh_from_db()
        
        self.assertTrue(submission.is_late)
        self.assertEqual(submission.status, SubmissionStatus.LATE)
    
    def test_grade_submission(self):
        """Test grading a submission."""
        submission = HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            submission_text="Answer"
        )
        submission.submit()
        
        submission.grade(score=Decimal("85.00"), feedback="Good work!")
        submission.refresh_from_db()
        
        self.assertEqual(submission.status, SubmissionStatus.GRADED)
        self.assertEqual(submission.score, Decimal("85.00"))
        self.assertEqual(submission.teacher_feedback, "Good work!")
        self.assertIsNotNone(submission.graded_at)
    
    def test_unique_submission_per_student(self):
        """Test one submission per student per homework."""
        HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            HomeworkSubmission.objects.create(
                homework=self.homework,
                student=self.student
            )


class HomeworkCompletionTest(TestCase):
    """Test completion rate calculation."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch, name="2025-2026",
            start_date=date(2025, 9, 1), end_date=date(2026, 6, 30)
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
        
        # Create 3 students
        self.students = []
        for i in range(3):
            student_user = User.objects.create_user(phone_number=f"+99890000000{i+2}")
            student_membership = BranchMembership.objects.create(
                user=student_user, branch=self.branch, role=BranchRole.STUDENT
            )
            student = StudentProfile.objects.create(user_branch=student_membership)
            ClassStudent.objects.create(
                class_obj=self.class_obj,
                membership=student_membership,
                is_active=True
            )
            self.students.append(student)
        
        self.homework = Homework.objects.create(
            class_subject=self.class_subject,
            title="Test",
            description="Test",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
    
    def test_completion_rate(self):
        """Test completion rate calculation."""
        # 2 out of 3 students submit
        for student in self.students[:2]:
            submission = HomeworkSubmission.objects.create(
                homework=self.homework,
                student=student
            )
            submission.submit()
        
        completion_rate = self.homework.get_completion_rate()
        self.assertEqual(completion_rate, 66.67)  # 2/3 * 100 ≈ 66.67
