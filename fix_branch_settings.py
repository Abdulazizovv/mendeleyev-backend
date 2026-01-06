#!/usr/bin/env python
"""Script to configure working days for branches."""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.branch.models import Branch, BranchSettings

print("=" * 80)
print("BRANCH SETTINGS CONFIGURATION")
print("=" * 80)

# Get all branches
branches = Branch.objects.filter(deleted_at__isnull=True)

print(f"\nFound {branches.count()} branch(es)")

for branch in branches:
    print(f"\n📍 Branch: {branch.name}")
    
    # Get or create branch settings
    settings, created = BranchSettings.objects.get_or_create(
        branch=branch,
        defaults={
            'working_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
            'holidays': [],
            'lesson_duration_minutes': 45,
            'break_duration_minutes': 10
        }
    )
    
    if created:
        print(f"   ✓ Created new settings")
    else:
        print(f"   ℹ Settings already exist")
    
    # Update working days if not set
    if not settings.working_days:
        settings.working_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        settings.save()
        print(f"   ✓ Updated working_days")
    
    print(f"   Current working days: {settings.working_days}")
    print(f"   Holidays configured: {len(settings.holidays or [])}")

print("\n" + "=" * 80)
print("CONFIGURATION COMPLETE!")
print("=" * 80)
print("\n✅ Now you can run the lesson generation tasks again:")
print("   - generate_weekly_lessons()")
print("   - generate_monthly_lessons()")
