#!/usr/bin/env python
"""Debug script to check why lessons are not being generated."""

import os
import sys
import django
from datetime import timedelta, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.school.schedule.models import TimetableTemplate, TimetableSlot
from apps.branch.models import BranchSettings
from apps.school.schedule.services import LessonGenerator
from django.utils import timezone

print("=" * 80)
print("LESSON GENERATION DEBUG REPORT")
print("=" * 80)

# Get all active timetables
timetables = TimetableTemplate.objects.filter(
    is_active=True,
    deleted_at__isnull=True
).select_related('branch', 'academic_year')

print(f"\n✓ Found {timetables.count()} active timetable(s)")

for timetable in timetables:
    print(f"\n{'='*80}")
    print(f"📋 Timetable: {timetable.name}")
    print(f"   Branch: {timetable.branch.name}")
    print(f"   Academic Year: {timetable.academic_year.name}")
    print(f"   Effective from: {timetable.effective_from}")
    print(f"   Effective until: {timetable.effective_until or 'Not set'}")
    print(f"   Is Active: {timetable.is_active}")
    
    # Check slots
    slots = TimetableSlot.objects.filter(
        timetable=timetable,
        deleted_at__isnull=True
    ).select_related('class_obj', 'class_subject', 'class_subject__subject', 'class_subject__teacher')
    
    print(f"\n📝 Slots: {slots.count()}")
    
    if slots.count() == 0:
        print("   ❌ ERROR: No slots found! You need to create slots first.")
        continue
    
    # Show first 5 slots as examples
    print("\n   Sample slots:")
    for slot in slots[:5]:
        print(f"   - {slot.day_of_week}: {slot.start_time}-{slot.end_time} | "
              f"{slot.class_obj.name} | {slot.class_subject.subject.name} | "
              f"Teacher: {slot.class_subject.teacher}")
    
    if slots.count() > 5:
        print(f"   ... and {slots.count() - 5} more slots")
    
    # Check branch settings
    print(f"\n🏢 Branch Settings:")
    branch_settings = BranchSettings.objects.filter(
        branch=timetable.branch
    ).first()
    
    if not branch_settings:
        print("   ❌ ERROR: Branch has no settings configured!")
        print("   You need to create BranchSettings with working_days and holidays.")
        continue
    
    print(f"   Working days: {branch_settings.working_days}")
    print(f"   Holidays: {len(branch_settings.holidays or [])} configured")
    
    if not branch_settings.working_days:
        print("   ❌ ERROR: No working days configured!")
        print("   Please set working_days in BranchSettings.")
        print("   Example: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']")
        continue
    
    # Test generation for next 7 days
    print(f"\n🔍 Testing generation for next 7 days:")
    today = timezone.now().date()
    start_date = today + timedelta(days=1)
    end_date = start_date + timedelta(days=6)
    
    print(f"   Date range: {start_date} to {end_date}")
    
    # Check each day
    day_map = LessonGenerator.get_working_days_map()
    working_days = branch_settings.working_days or []
    holidays = branch_settings.holidays or []
    
    for i in range(7):
        test_date = start_date + timedelta(days=i)
        weekday_num = test_date.weekday()
        day_name = [k for k, v in day_map.items() if v == weekday_num][0]
        
        is_working = LessonGenerator.is_working_day(test_date, working_days)
        is_holiday = LessonGenerator.is_holiday(test_date, holidays)
        day_slots = slots.filter(day_of_week=day_name)
        
        status = "✓" if is_working and not is_holiday else "✗"
        print(f"   {status} {test_date} ({day_name}): ", end="")
        
        if is_holiday:
            print("Holiday - SKIPPED")
        elif not is_working:
            print("Not a working day - SKIPPED")
        else:
            print(f"Working day - {day_slots.count()} slots to generate")
    
    # Try actual generation
    print(f"\n🚀 Attempting to generate lessons...")
    try:
        created, skipped = LessonGenerator.generate_lessons_for_period(
            timetable=timetable,
            start_date=start_date,
            end_date=end_date,
            skip_existing=True
        )
        print(f"   ✓ Success!")
        print(f"   Created: {created}")
        print(f"   Skipped: {skipped}")
        
        if created == 0 and skipped == 0:
            print(f"\n   ⚠️  WARNING: Nothing was created or skipped!")
            print(f"   This means:")
            print(f"   - Either no working days match your slot days")
            print(f"   - Or slots day_of_week doesn't match working_days format")
            print(f"\n   Slot days in database:")
            unique_days = slots.values_list('day_of_week', flat=True).distinct()
            for day in unique_days:
                print(f"   - {day}")
            print(f"\n   Working days in settings:")
            for day in working_days:
                print(f"   - {day}")
                
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("DEBUG REPORT COMPLETE")
print("=" * 80)
