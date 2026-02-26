#!/usr/bin/env python
"""
Yangi studentlar bilan tez test
"""
import os
import sys
import django
from io import BytesIO
from openpyxl import Workbook

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.school.students.tasks import import_students_task
from apps.branch.models import Branch

# Excel yaratish
wb = Workbook()
ws = wb.active

# Header
ws.append(['Shartnoma', 'FIO', 'Balans', 'Sinf', 'Guruh', 'Telefon', 'Sinf Rahbari', 'Jinsi', "Tug'ilgan kuni", 'Manzil'])

# YANGI telefon raqamlar bilan test data
ws.append(['TEST-001', 'Yangi Test Testovich', 500000, '11-A', '-', '+998770001111', '-', 'male', '2008-01-15', 'Test Address'])
ws.append(['TEST-002', 'Yangi Testa Testovna', 750000, '11-B', '-', '+998770002222', '-', 'female', '2009-02-20', 'Test Address 2'])
ws.append(['TEST-003', 'Yangi Ali Testovich', 1000000, '10-C', '-', '+998770003333', '-', 'male', '2010-03-25', 'Test Address 3'])

# BytesIO ga saqlash
excel_file = BytesIO()
wb.save(excel_file)
excel_file.seek(0)

# File content
file_content = excel_file.read()

# Branch
branch = Branch.objects.filter(name__icontains='Qo\'qon').first()

print("\n" + "="*80)
print("YANGI STUDENTLAR BILAN TEST")
print("="*80)
print(f"\nBranch: {branch.name} ({branch.id})")
print("Telefon raqamlar: +998770001111, +998770002222, +998770003333")
print("\nImport boshlanmoqda...\n")

# Import (dry_run=False)
result = import_students_task(file_content, str(branch.id), dry_run=False)

print("\n" + "="*80)
print("NATIJA:")
print("="*80)
print(f"Total: {result['total']}")
print(f"Success: {result['success']}")
print(f"Skipped: {result['skipped']}")
print(f"Failed: {result['failed']}")

if result.get('errors'):
    print(f"\nXatolar ({len(result['errors'])}):")
    for err in result['errors'][:5]:
        print(f"  - Row {err.get('row')}: {err.get('error')}")

if result.get('students'):
    print(f"\nYaratilgan studentlar ({len(result['students'])}):")
    for s in result['students'][:5]:
        print(f"  - {s.get('name')} ({s.get('phone')}): {s.get('personal_number')}")

# Tranzaksiyalarni tekshirish
print("\n" + "="*80)
print("TRANZAKSIYALAR VA BALANSLAR:")
print("="*80)

from apps.school.finance.models import Transaction, StudentBalance
from auth.profiles.models import StudentProfile

test_phones = ['+998770001111', '+998770002222', '+998770003333']
for phone in test_phones:
    from auth.users.models import User
    user = User.objects.filter(phone_number=phone).first()
    if user:
        profile = StudentProfile.objects.filter(
            user_branch__user=user,
            user_branch__branch=branch
        ).first()
        if profile:
            # Balance
            balance = StudentBalance.objects.filter(student_profile=profile).first()
            balance_amount = balance.balance if balance else 0
            
            # Tranzaksiyalar
            txns = Transaction.objects.filter(
                student_profile=profile,
                metadata__source='student_import'
            )
            txn_count = txns.count()
            txn_total = sum(t.amount for t in txns)
            
            # Sinf
            from apps.school.classes.models import ClassStudent
            class_student = ClassStudent.objects.filter(
                membership=profile.user_branch,
                deleted_at__isnull=True
            ).first()
            class_name = class_student.class_obj.name if class_student else "YO'Q"
            
            print(f"\n{profile} ({phone}):")
            print(f"  Balance: {balance_amount:,} so'm")
            print(f"  Tranzaksiyalar: {txn_count} ta ({txn_total:,} so'm)")
            print(f"  Sinf: {class_name}")
        else:
            print(f"\n{phone}: Profile topilmadi")
    else:
        print(f"\n{phone}: User topilmadi")

print("\n" + "="*80)
