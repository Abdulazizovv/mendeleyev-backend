#!/usr/bin/env python
"""Test Celery tasks for lesson generation."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.school.schedule.tasks import generate_weekly_lessons, generate_monthly_lessons

print("=" * 80)
print("TESTING CELERY LESSON GENERATION TASKS")
print("=" * 80)

# Test weekly lessons
print("\n📅 Testing generate_weekly_lessons()...")
result_weekly = generate_weekly_lessons()
print(f"✓ Weekly lessons result:")
for key, value in result_weekly.items():
    print(f"   {key}: {value}")

# Test monthly lessons
print("\n📅 Testing generate_monthly_lessons()...")
result_monthly = generate_monthly_lessons()
print(f"✓ Monthly lessons result:")
for key, value in result_monthly.items():
    print(f"   {key}: {value}")

print("\n" + "=" * 80)
print("TESTING COMPLETE!")
print("=" * 80)
