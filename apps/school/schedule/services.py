"""Services for schedule management and lesson generation."""
from django.db.models import Q
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
from .models import (
    TimetableSlot, LessonInstance, TimetableTemplate, 
    DayOfWeek, LessonStatus
)
from apps.branch.models import BranchSettings


class ConflictType:
    """Types of schedule conflicts."""
    TEACHER = 'teacher'
    ROOM = 'room'
    TIME_OVERLAP = 'time_overlap'


class ScheduleConflictDetector:
    """Service for detecting schedule conflicts."""
    
    @staticmethod
    def check_slot_conflicts(slot: TimetableSlot, exclude_slot_id=None) -> List[Dict]:
        """
        Check if a timetable slot has conflicts.
        
        Returns list of conflicts with details:
        [
            {
                'type': 'teacher',
                'message': 'Teacher conflict',
                'conflicting_slot': TimetableSlot instance
            }
        ]
        """
        conflicts = []
        
        # Query overlapping slots (same day, same time range)
        overlapping_slots = TimetableSlot.objects.filter(
            timetable=slot.timetable,
            day_of_week=slot.day_of_week,
            deleted_at__isnull=True
        ).filter(
            # Time overlap: (start1 < end2) AND (end1 > start2)
            Q(start_time__lt=slot.end_time) & Q(end_time__gt=slot.start_time)
        )
        
        if exclude_slot_id:
            overlapping_slots = overlapping_slots.exclude(id=exclude_slot_id)
        
        for conflicting_slot in overlapping_slots:
            # Check teacher conflict
            if (slot.class_subject.teacher_id == 
                conflicting_slot.class_subject.teacher_id):
                conflicts.append({
                    'type': ConflictType.TEACHER,
                    'message': (
                        f"O'qituvchi {slot.class_subject.teacher} bir vaqtda "
                        f"ikki joyda dars o'ta olmaydi."
                    ),
                    'conflicting_slot': conflicting_slot,
                    'details': {
                        'teacher': str(slot.class_subject.teacher),
                        'class': str(conflicting_slot.class_obj),
                        'time': f"{conflicting_slot.start_time} - {conflicting_slot.end_time}"
                    }
                })
            
            # Check room conflict
            if slot.room and conflicting_slot.room and slot.room_id == conflicting_slot.room_id:
                conflicts.append({
                    'type': ConflictType.ROOM,
                    'message': (
                        f"Xona {slot.room.name} bir vaqtda "
                        f"ikki sinf uchun band bo'lishi mumkin emas."
                    ),
                    'conflicting_slot': conflicting_slot,
                    'details': {
                        'room': str(slot.room),
                        'class': str(conflicting_slot.class_obj),
                        'time': f"{conflicting_slot.start_time} - {conflicting_slot.end_time}"
                    }
                })
        
        return conflicts
    
    @staticmethod
    def check_lesson_conflicts(lesson: LessonInstance, exclude_lesson_id=None) -> List[Dict]:
        """
        Check if a lesson instance has conflicts.
        
        Similar to slot conflicts but for actual lesson instances on specific dates.
        """
        conflicts = []
        
        # Query overlapping lessons on same date
        overlapping_lessons = LessonInstance.objects.filter(
            date=lesson.date,
            deleted_at__isnull=True
        ).filter(
            # Time overlap
            Q(start_time__lt=lesson.end_time) & Q(end_time__gt=lesson.start_time)
        ).exclude(
            status=LessonStatus.CANCELED
        )
        
        if exclude_lesson_id:
            overlapping_lessons = overlapping_lessons.exclude(id=exclude_lesson_id)
        
        for conflicting_lesson in overlapping_lessons:
            # Check teacher conflict
            if (lesson.class_subject.teacher_id == 
                conflicting_lesson.class_subject.teacher_id):
                conflicts.append({
                    'type': ConflictType.TEACHER,
                    'message': (
                        f"O'qituvchi {lesson.teacher} {lesson.date} sanasida "
                        f"{lesson.start_time} da ikki joyda dars o'ta olmaydi."
                    ),
                    'conflicting_lesson': conflicting_lesson,
                    'details': {
                        'teacher': str(lesson.teacher),
                        'class': str(conflicting_lesson.class_obj),
                        'time': f"{conflicting_lesson.start_time} - {conflicting_lesson.end_time}"
                    }
                })
            
            # Check room conflict
            if lesson.room and conflicting_lesson.room and lesson.room_id == conflicting_lesson.room_id:
                conflicts.append({
                    'type': ConflictType.ROOM,
                    'message': (
                        f"Xona {lesson.room.name} {lesson.date} sanasida "
                        f"{lesson.start_time} da ikki sinf uchun band."
                    ),
                    'conflicting_lesson': conflicting_lesson,
                    'details': {
                        'room': str(lesson.room),
                        'class': str(conflicting_lesson.class_obj),
                        'time': f"{conflicting_lesson.start_time} - {conflicting_lesson.end_time}"
                    }
                })
        
        return conflicts
    
    @staticmethod
    def validate_slot_no_conflicts(slot: TimetableSlot, exclude_slot_id=None):
        """
        Validate that slot has no conflicts. Raise ValidationError if conflicts exist.
        """
        conflicts = ScheduleConflictDetector.check_slot_conflicts(slot, exclude_slot_id)
        if conflicts:
            error_messages = [c['message'] for c in conflicts]
            raise ValidationError({
                'non_field_errors': error_messages,
                'conflicts': conflicts
            })
    
    @staticmethod
    def validate_lesson_no_conflicts(lesson: LessonInstance, exclude_lesson_id=None):
        """
        Validate that lesson has no conflicts. Raise ValidationError if conflicts exist.
        """
        conflicts = ScheduleConflictDetector.check_lesson_conflicts(lesson, exclude_lesson_id)
        if conflicts:
            error_messages = [c['message'] for c in conflicts]
            raise ValidationError({
                'non_field_errors': error_messages,
                'conflicts': conflicts
            })


class LessonGenerator:
    """Service for generating lesson instances from timetable."""
    
    @staticmethod
    def get_working_days_map() -> Dict[str, int]:
        """Map day names to weekday numbers (0=Monday, 6=Sunday)."""
        return {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }
    
    @staticmethod
    def is_holiday(date: date, holidays: List[str]) -> bool:
        """Check if a date is a holiday."""
        date_str = date.strftime('%Y-%m-%d')
        return date_str in holidays
    
    @staticmethod
    def is_working_day(date: date, working_days: List[str]) -> bool:
        """Check if a date is a working day."""
        day_map = LessonGenerator.get_working_days_map()
        weekday = date.weekday()
        
        # Convert working_days names to weekday numbers
        working_weekdays = [day_map.get(day.lower()) for day in working_days if day.lower() in day_map]
        
        return weekday in working_weekdays
    
    @staticmethod
    def get_date_range(start_date: date, end_date: date) -> List[date]:
        """Generate list of dates between start and end (inclusive)."""
        dates = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)
        return dates
    
    @staticmethod
    def generate_lessons_for_period(
        timetable: TimetableTemplate,
        start_date: date,
        end_date: date,
        skip_existing: bool = True
    ) -> Tuple[int, int]:
        """
        Generate lesson instances from timetable for a date range.
        
        Args:
            timetable: TimetableTemplate to generate from
            start_date: Start date for generation
            end_date: End date for generation
            skip_existing: If True, skip dates that already have lessons
        
        Returns:
            (created_count, skipped_count) tuple
        """
        # Get branch settings
        branch_settings = BranchSettings.objects.filter(
            branch=timetable.branch
        ).first()
        
        if not branch_settings:
            raise ValueError(f"Branch {timetable.branch} has no settings configured.")
        
        working_days = branch_settings.working_days or []
        holidays = branch_settings.holidays or []
        
        # Get all slots for this timetable
        slots = TimetableSlot.objects.filter(
            timetable=timetable,
            deleted_at__isnull=True
        ).select_related('class_subject', 'class_obj', 'room')
        
        if not slots.exists():
            raise ValueError("Timetable has no slots configured.")
        
        # Map day names to weekdays
        day_map = LessonGenerator.get_working_days_map()
        
        created_count = 0
        skipped_count = 0
        
        # Generate dates
        for current_date in LessonGenerator.get_date_range(start_date, end_date):
            # Skip if holiday
            if LessonGenerator.is_holiday(current_date, holidays):
                continue
            
            # Skip if not a working day
            if not LessonGenerator.is_working_day(current_date, working_days):
                continue
            
            # Get weekday name
            weekday_num = current_date.weekday()
            day_name = [k for k, v in day_map.items() if v == weekday_num][0]
            
            # Get slots for this day
            day_slots = slots.filter(day_of_week=day_name)
            
            for slot in day_slots:
                # Check if lesson already exists
                if skip_existing:
                    exists = LessonInstance.objects.filter(
                        class_subject=slot.class_subject,
                        date=current_date,
                        lesson_number=slot.lesson_number,
                        deleted_at__isnull=True
                    ).exists()
                    
                    if exists:
                        skipped_count += 1
                        continue
                
                # Create lesson instance
                LessonInstance.objects.create(
                    class_subject=slot.class_subject,
                    date=current_date,
                    lesson_number=slot.lesson_number,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    room=slot.room,
                    status=LessonStatus.PLANNED,
                    is_auto_generated=True,
                    timetable_slot=slot
                )
                created_count += 1
        
        return created_count, skipped_count
    
    @staticmethod
    def generate_lessons_for_week(
        timetable: TimetableTemplate,
        week_start: date
    ) -> Tuple[int, int]:
        """
        Generate lessons for one week.
        
        Args:
            timetable: TimetableTemplate to generate from
            week_start: Monday of the week to generate
        
        Returns:
            (created_count, skipped_count) tuple
        """
        week_end = week_start + timedelta(days=6)
        return LessonGenerator.generate_lessons_for_period(
            timetable, week_start, week_end
        )
    
    @staticmethod
    def generate_lessons_for_month(
        timetable: TimetableTemplate,
        year: int,
        month: int
    ) -> Tuple[int, int]:
        """
        Generate lessons for one month.
        
        Args:
            timetable: TimetableTemplate to generate from
            year: Year
            month: Month (1-12)
        
        Returns:
            (created_count, skipped_count) tuple
        """
        from calendar import monthrange
        
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        return LessonGenerator.generate_lessons_for_period(
            timetable, start_date, end_date
        )
    
    @staticmethod
    def generate_lessons_for_quarter(
        timetable: TimetableTemplate,
        quarter
    ) -> Tuple[int, int]:
        """
        Generate lessons for an entire quarter.
        
        Args:
            timetable: TimetableTemplate to generate from
            quarter: Quarter instance
        
        Returns:
            (created_count, skipped_count) tuple
        """
        return LessonGenerator.generate_lessons_for_period(
            timetable, quarter.start_date, quarter.end_date
        )
