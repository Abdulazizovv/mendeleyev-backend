from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta
from apps.branch.models import Branch, BranchStatuses, BranchMembership, BranchRole, BranchSettings
from apps.school.academic.models import AcademicYear, Quarter
from apps.school.classes.models import Class
from apps.school.subjects.models import Subject, ClassSubject
from apps.school.rooms.models import Room
from apps.school.schedule.models import (
    TimetableTemplate, TimetableSlot, LessonInstance, LessonTopic, LessonStatus
)
from apps.school.schedule.services import ScheduleConflictDetector, LessonGenerator
from auth.profiles.models import TeacherProfile

User = get_user_model()


class TimetableTemplateModelTest(TestCase):
    """Test TimetableTemplate model validation and constraints."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_active=True
        )
    
    def test_create_timetable_template(self):
        """Test basic timetable template creation."""
        template = TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Fall 2025",
            effective_from=date(2025, 9, 1),
            is_active=True
        )
        self.assertEqual(template.name, "Fall 2025")
        self.assertTrue(template.is_active)
    
    def test_unique_active_template_per_year(self):
        """Test that only one template can be active per academic year."""
        TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Template 1",
            effective_from=date(2025, 9, 1),
            is_active=True
        )
        
        # Creating another active template should violate constraint
        with self.assertRaises(Exception):  # IntegrityError
            TimetableTemplate.objects.create(
                branch=self.branch,
                academic_year=self.academic_year,
                name="Template 2",
                effective_from=date(2025, 9, 1),
                is_active=True
            )
    
    def test_multiple_inactive_templates_allowed(self):
        """Test that multiple inactive templates can exist."""
        TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Template 1",
            effective_from=date(2025, 9, 1),
            is_active=False
        )
        TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Template 2",
            effective_from=date(2025, 10, 1),
            is_active=False
        )
        self.assertEqual(TimetableTemplate.objects.filter(is_active=False).count(), 2)


class TimetableSlotModelTest(TestCase):
    """Test TimetableSlot model validation and conflict detection."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_active=True
        )
        self.template = TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Main Template",
            effective_from=date(2025, 9, 1),
            is_active=True
        )
        self.class_obj = Class.objects.create(
            branch=self.branch,
            name="5A",
            grade_level=5,
            academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(
            branch=self.branch,
            name="Mathematics"
        )
        
        # Create teacher
        self.user = User.objects.create_user(phone_number="+998900000001")
        self.membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user_branch=self.membership)
        
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj,
            subject=self.subject,
            teacher=self.teacher
        )
        self.room = Room.objects.create(
            branch=self.branch,
            name="Room 101",
            room_type="classroom"
        )
    
    def test_create_slot(self):
        """Test basic slot creation."""
        slot = TimetableSlot.objects.create(
            timetable=self.template,
            class_subject=self.class_subject,
            day_of_week=0,  # Monday
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        self.assertEqual(slot.day_of_week, 0)
        self.assertEqual(slot.lesson_number, 1)
    
    def test_unique_slot_per_class_day_lesson(self):
        """Test uniqueness constraint for class/day/lesson."""
        TimetableSlot.objects.create(
            timetable=self.template,
            class_subject=self.class_subject,
            day_of_week=0,
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            TimetableSlot.objects.create(
                timetable=self.template,
                class_subject=self.class_subject,
                day_of_week=0,
                lesson_number=1,
                start_time=time(9, 0),
                end_time=time(9, 45),
                room=self.room
            )


class ScheduleConflictDetectorTest(TestCase):
    """Test conflict detection service."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_active=True
        )
        self.template = TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Main",
            effective_from=date(2025, 9, 1),
            is_active=True
        )
        
        # Create two classes
        self.class_5a = Class.objects.create(
            branch=self.branch, name="5A", grade_level=5, academic_year=self.academic_year
        )
        self.class_5b = Class.objects.create(
            branch=self.branch, name="5B", grade_level=5, academic_year=self.academic_year
        )
        
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        
        # One teacher for both classes
        self.user = User.objects.create_user(phone_number="+998900000001")
        self.membership = BranchMembership.objects.create(
            user=self.user, branch=self.branch, role=BranchRole.TEACHER
        )
        self.teacher = TeacherProfile.objects.create(user_branch=self.membership)
        
        self.cs_5a = ClassSubject.objects.create(
            class_obj=self.class_5a, subject=self.subject, teacher=self.teacher
        )
        self.cs_5b = ClassSubject.objects.create(
            class_obj=self.class_5b, subject=self.subject, teacher=self.teacher
        )
        
        self.room = Room.objects.create(branch=self.branch, name="Room 101", room_type="classroom")
        
        self.detector = ScheduleConflictDetector()
    
    def test_no_conflict_different_times(self):
        """Test no conflict when slots are at different times."""
        slot1 = TimetableSlot.objects.create(
            timetable=self.template,
            class_subject=self.cs_5a,
            day_of_week=0,
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        
        conflicts = self.detector.check_slot_conflicts(slot1)
        self.assertEqual(conflicts, [])
    
    def test_teacher_conflict(self):
        """Test teacher double-booking detection."""
        # Slot 1: 5A with teacher at 8:00-8:45
        TimetableSlot.objects.create(
            timetable=self.template,
            class_subject=self.cs_5a,
            day_of_week=0,
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        
        # Slot 2: 5B with same teacher at same time
        slot2 = TimetableSlot(
            timetable=self.template,
            class_subject=self.cs_5b,
            day_of_week=0,
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45)
        )
        
        conflicts = self.detector.check_slot_conflicts(slot2)
        self.assertGreater(len(conflicts), 0)
        self.assertIn("teacher", conflicts[0].lower())
    
    def test_room_conflict(self):
        """Test room double-booking detection."""
        # Create another class subject with different teacher
        user2 = User.objects.create_user(phone_number="+998900000002")
        membership2 = BranchMembership.objects.create(
            user=user2, branch=self.branch, role=BranchRole.TEACHER
        )
        teacher2 = TeacherProfile.objects.create(user_branch=membership2)
        
        cs_other = ClassSubject.objects.create(
            class_obj=self.class_5b, subject=self.subject, teacher=teacher2
        )
        
        # Slot 1: Room at 8:00-8:45
        TimetableSlot.objects.create(
            timetable=self.template,
            class_subject=self.cs_5a,
            day_of_week=0,
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        
        # Slot 2: Same room at same time
        slot2 = TimetableSlot(
            timetable=self.template,
            class_subject=cs_other,
            day_of_week=0,
            lesson_number=2,  # Different lesson number for same class
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        
        conflicts = self.detector.check_slot_conflicts(slot2)
        self.assertGreater(len(conflicts), 0)
        self.assertIn("room", conflicts[0].lower())


class LessonGeneratorTest(TestCase):
    """Test automated lesson generation service."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        
        # Configure branch settings with working days
        self.settings = BranchSettings.objects.get(branch=self.branch)
        self.settings.working_days = [0, 1, 2, 3, 4]  # Mon-Fri
        self.settings.holidays = []
        self.settings.save()
        
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30),
            is_active=True
        )
        self.template = TimetableTemplate.objects.create(
            branch=self.branch,
            academic_year=self.academic_year,
            name="Main",
            effective_from=date(2025, 9, 1),
            is_active=True
        )
        
        self.class_obj = Class.objects.create(
            branch=self.branch, name="5A", grade_level=5, academic_year=self.academic_year
        )
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        
        user = User.objects.create_user(phone_number="+998900000001")
        membership = BranchMembership.objects.create(
            user=user, branch=self.branch, role=BranchRole.TEACHER
        )
        teacher = TeacherProfile.objects.create(user_branch=membership)
        
        self.class_subject = ClassSubject.objects.create(
            class_obj=self.class_obj, subject=self.subject, teacher=teacher
        )
        
        self.room = Room.objects.create(branch=self.branch, name="Room 101", room_type="classroom")
        
        # Create slot for Monday lesson 1
        self.slot = TimetableSlot.objects.create(
            timetable=self.template,
            class_subject=self.class_subject,
            day_of_week=0,  # Monday
            lesson_number=1,
            start_time=time(8, 0),
            end_time=time(8, 45),
            room=self.room
        )
        
        self.generator = LessonGenerator(self.template)
    
    def test_generate_lessons_for_week(self):
        """Test lesson generation for a week."""
        start = date(2026, 1, 5)  # Monday
        end = date(2026, 1, 11)  # Sunday
        
        lessons = self.generator.generate_lessons_for_period(start, end)
        
        # Should generate 1 lesson (Monday only)
        self.assertGreater(len(lessons), 0)
        self.assertEqual(lessons[0].class_subject, self.class_subject)
        self.assertEqual(lessons[0].lesson_number, 1)
        self.assertTrue(lessons[0].is_auto_generated)
    
    def test_skip_weekends(self):
        """Test that generator skips weekends."""
        start = date(2026, 1, 5)  # Monday
        end = date(2026, 1, 11)  # Sunday
        
        lessons = self.generator.generate_lessons_for_period(start, end)
        
        # Check no lessons on Saturday/Sunday
        for lesson in lessons:
            day_of_week = lesson.date.weekday()
            self.assertNotIn(day_of_week, [5, 6])  # Sat, Sun
    
    def test_skip_holidays(self):
        """Test that generator respects holidays."""
        # Set Monday as holiday
        self.settings.holidays = ["2026-01-05"]
        self.settings.save()
        
        start = date(2026, 1, 5)  # Monday (holiday)
        end = date(2026, 1, 5)
        
        lessons = self.generator.generate_lessons_for_period(start, end)
        
        # Should not generate lessons on holiday
        self.assertEqual(len(lessons), 0)
    
    def test_idempotent_generation(self):
        """Test that re-running generation doesn't create duplicates."""
        start = date(2026, 1, 5)
        end = date(2026, 1, 5)
        
        lessons1 = self.generator.generate_lessons_for_period(start, end)
        count1 = LessonInstance.objects.filter(date=start).count()
        
        # Run again with skip_existing=True
        lessons2 = self.generator.generate_lessons_for_period(start, end, skip_existing=True)
        count2 = LessonInstance.objects.filter(date=start).count()
        
        self.assertEqual(count1, count2)


class LessonTopicModelTest(TestCase):
    """Test LessonTopic ordering and validation."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        self.subject = Subject.objects.create(branch=self.branch, name="Math")
        self.academic_year = AcademicYear.objects.create(
            branch=self.branch,
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 6, 30)
        )
        self.quarter = Quarter.objects.create(
            academic_year=self.academic_year,
            name="Q1",
            number=1,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 11, 30)
        )
    
    def test_manual_topic_ordering(self):
        """Test manual position-based ordering."""
        topic1 = LessonTopic.objects.create(
            subject=self.subject,
            quarter=self.quarter,
            title="Introduction",
            position=1
        )
        topic2 = LessonTopic.objects.create(
            subject=self.subject,
            quarter=self.quarter,
            title="Advanced",
            position=2
        )
        
        topics = LessonTopic.objects.filter(subject=self.subject, quarter=self.quarter).order_by('position')
        self.assertEqual(list(topics), [topic1, topic2])
    
    def test_unique_position_per_subject_quarter(self):
        """Test that position is unique per subject/quarter."""
        LessonTopic.objects.create(
            subject=self.subject,
            quarter=self.quarter,
            title="Topic 1",
            position=1
        )
        
        with self.assertRaises(Exception):  # IntegrityError
            LessonTopic.objects.create(
                subject=self.subject,
                quarter=self.quarter,
                title="Topic 2",
                position=1  # Duplicate position
            )
