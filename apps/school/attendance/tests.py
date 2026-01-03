from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta
from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole
from apps.school.academic.models import AcademicYear
from apps.school.classes.models import Class, ClassStudent
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.attendance.models import LessonAttendance, StudentAttendanceRecord, AttendanceStatus
from apps.school.schedule.models import LessonInstance
from auth.profiles.models import TeacherProfile, StudentProfile

User = get_user_model()


class LessonAttendanceModelTest(TestCase):
    """Test LessonAttendance model and locking mechanism."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30)
        )
        self.class_obj = Class.objects.create(
            branch=self.branch, name="5A", grade_level=5, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        
        user = User.objects.create_user(phone_number="+998900000001")
        membership = BranchMembership.objects.create(
            user=user, branch=self.branch, role=BranchRole.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user_branch=membership)
        
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj, subject=self.subject, teacher=self.teacher
        )
    
    def test_create_attendance(self):
        """Test basic attendance creation."""
        attendance = LessonAttendance.objects.create(
            class_subject=self.class_subject,
            date=date.today(),
            lesson_number=1
        )
        self.assertFalse(attendance.is_locked)
        self.assertIsNone(attendance.locked_at)
    
    def test_lock_attendance(self):
        """Test locking attendance."""
        attendance = LessonAttendance.objects.create(
            class_subject=self.class_subject,
            date=date.today(),
            lesson_number=1
        )
        
        attendance.lock(locked_by=self.teacher.membership.user)
        attendance.refresh_from_db()
        
        self.assertTrue(attendance.is_locked)
        self.assertIsNotNone(attendance.locked_at)
        self.assertEqual(attendance.locked_by, self.teacher.membership.user)
    
    def test_unlock_attendance(self):
        """Test unlocking attendance (admin override)."""
        attendance = LessonAttendance.objects.create(
            class_subject=self.class_subject,
            date=date.today(),
            lesson_number=1
        )
        
        attendance.lock()
        attendance.unlock()
        attendance.refresh_from_db()
        
        self.assertFalse(attendance.is_locked)
        self.assertIsNone(attendance.locked_at)


class StudentAttendanceRecordTest(TestCase):
    """Test individual student attendance records."""
    
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
        
        self.attendance = LessonAttendance.objects.create(
            class_subject=self.class_subject,
            date=date.today(),
            lesson_number=1
        )
        
        # Create student
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
    
    def test_create_attendance_record(self):
        """Test creating student attendance record."""
        record = StudentAttendanceRecord.objects.create(
            attendance=self.attendance,
            student=self.student,
            status=AttendanceStatus.PRESENT
        )
        self.assertEqual(record.status, AttendanceStatus.PRESENT)
    
    def test_unique_record_per_student(self):
        """Test uniqueness constraint."""
        StudentAttendanceRecord.objects.create(
            attendance=self.attendance,
            student=self.student,
            status=AttendanceStatus.PRESENT
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            StudentAttendanceRecord.objects.create(
                attendance=self.attendance,
                student=self.student,
                status=AttendanceStatus.ABSENT
            )


class AttendanceStatisticsTest(TestCase):
    """Test attendance statistics calculation."""
    
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
        
        # Create student
        student_user = User.objects.create_user(phone_number="+998900000002")
        student_membership = BranchMembership.objects.create(
            user=student_user, branch=self.branch, role=BranchRole.STUDENT
        )
        self.student = StudentProfile.objects.create(user_branch=student_membership)
        
        # Create attendance records
        for i in range(5):
            attendance = LessonAttendance.objects.create(
                class_subject=self.class_subject,
                date=date.today() - timedelta(days=i),
                lesson_number=1
            )
            StudentAttendanceRecord.objects.create(
                attendance=attendance,
                student=self.student,
                status=AttendanceStatus.PRESENT if i < 4 else AttendanceStatus.ABSENT
            )
    
    def test_attendance_rate_calculation(self):
        """Test attendance rate is calculated correctly."""
        from apps.school.attendance.models import AttendanceStatistics
        
        stats = AttendanceStatistics.objects.create(
            student=self.student,
            class_subject=self.class_subject,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today()
        )
        stats.calculate()
        stats.refresh_from_db()
        
        # 4 present out of 5 = 80%
        self.assertEqual(stats.total_lessons, 5)
        self.assertEqual(stats.present_count, 4)
        self.assertEqual(stats.absent_count, 1)
        self.assertEqual(float(stats.attendance_rate), 80.0)
