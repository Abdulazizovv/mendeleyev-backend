#!/usr/bin/env python
"""
API orqali balansli student import testlari
"""
import os
import sys
import django
import time
from io import BytesIO
from openpyxl import Workbook

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.finance.models import Transaction, StudentBalance
from auth.profiles.models import StudentProfile

User = get_user_model()


def create_test_excel():
    """Test Excel yaratish"""
    wb = Workbook()
    ws = wb.active
    
    # Header
    ws.append(['Shartnoma', 'FIO', 'Balans', 'Sinf', 'Guruh', 'Telefon', 'Sinf Rahbari', 'Jinsi', "Tug'ilgan kuni", 'Manzil'])
    
    # Test studentlar - yangi telefon raqamlar
    test_data = [
        ['API-001', 'API-Test Testov Testovich', 750000, '11-A', '-', '+998909999991', '-', 'male', '2008-05-20', 'API Test Address 1'],
        ['API-002', 'API-Testa Testova Testovna', 1250000, '11-B', '-', '+998909999992', '-', 'female', '2009-03-15', 'API Test Address 2'],
        ['API-003', 'API-Ali Sinov Sinovich', 500000, '10-C', '-', '+998909999993', '-', 'male', '2010-07-10', 'API Test Address 3'],
    ]
    
    for row in test_data:
        ws.append(row)
    
    # BytesIO ga saqlash
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    return excel_file


def main():
    print("\n" + "="*80)
    print("API ORQALI BALANSLI STUDENT IMPORT TEST")
    print("="*80)
    
    # 1. Admin user yaratish/topish
    print("\n1. Admin user setup...")
    admin_phone = '+998991234567'
    admin_user, created = User.objects.get_or_create(
        phone_number=admin_phone,
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'phone_verified': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
    
    # Branch topish
    branch = Branch.objects.filter(name__icontains='Qo\'qon').first()
    if not branch:
        print("   ✗ Branch topilmadi!")
        return
    
    # Admin membership
    admin_membership, _ = BranchMembership.objects.get_or_create(
        user=admin_user,
        branch=branch,
        defaults={
            'role': BranchRole.SUPER_ADMIN,
            'balance': 0
        }
    )
    
    print(f"   ✓ Admin: {admin_user.phone_number}")
    print(f"   ✓ Branch: {branch.name} ({branch.id})")
    
    # 2. Login
    print("\n2. Login...")
    client = Client()
    # Note: Bu test login - production da token auth ishlatiladi
    client.force_login(admin_user)
    print("   ✓ Logged in")
    
    # 3. Excel yaratish
    print("\n3. Excel yaratish...")
    excel_file = create_test_excel()
    print(f"   ✓ Excel yaratildi")
    
    # 4. Import API chaqirish (dry_run=True)
    print("\n4. Dry run import...")
    response = client.post(
        '/api/school/students/import/',
        {
            'file': excel_file,
            'branch_id': str(branch.id),
            'dry_run': 'true'
        },
        format='multipart'
    )
    
    if response.status_code != 200:
        print(f"   ✗ Dry run xatosi: {response.status_code}")
        print(f"   Response: {response.json()}")
        return
    
    dry_run_data = response.json()
    task_id = dry_run_data.get('task_id')
    print(f"   ✓ Task ID: {task_id}")
    
    # Status polling
    print("   Polling...")
    for i in range(30):
        time.sleep(1)
        status_response = client.get(f'/api/school/students/import-status/{task_id}/')
        status_data = status_response.json()
        state = status_data.get('status')
        
        if state == 'SUCCESS':
            result = status_data.get('result', {})
            print(f"   ✓ Total: {result.get('total')}")
            print(f"   ✓ Will create: {result.get('success')}")
            print(f"   ✓ Already exists: {result.get('skipped')}")
            break
        elif state == 'FAILURE':
            print(f"   ✗ Task failed: {status_data}")
            return
        else:
            print(f"   ... waiting ({i+1}s): {state}")
    
    # 5. Haqiqiy import (dry_run=False)
    print("\n5. Haqiqiy import...")
    excel_file.seek(0)  # Reset file pointer
    
    response = client.post(
        '/api/school/students/import/',
        {
            'file': excel_file,
            'branch_id': str(branch.id),
            'dry_run': 'false'
        },
        format='multipart'
    )
    
    if response.status_code != 200:
        print(f"   ✗ Import xatosi: {response.status_code}")
        print(f"   Response: {response.json()}")
        return
    
    import_data = response.json()
    task_id = import_data.get('task_id')
    print(f"   ✓ Task ID: {task_id}")
    
    # Status polling
    print("   Polling...")
    for i in range(30):
        time.sleep(1)
        status_response = client.get(f'/api/school/students/import-status/{task_id}/')
        status_data = status_response.json()
        state = status_data.get('status')
        
        if state == 'SUCCESS':
            result = status_data.get('result', {})
            print(f"   ✓ Total: {result.get('total')}")
            print(f"   ✓ Created: {result.get('success')}")
            print(f"   ✓ Skipped: {result.get('skipped')}")
            
            if result.get('errors'):
                print("\n   Xatolar:")
                for error in result['errors'][:3]:
                    print(f"     - Row {error.get('row', '?')}: {error.get('error', '')}")
            break
        elif state == 'FAILURE':
            print(f"   ✗ Task failed: {status_data}")
            return
        else:
            print(f"   ... waiting ({i+1}s): {state}")
    
    # 6. Natijalarni tekshirish
    print("\n6. Natijalarni tekshirish...")
    
    # Import tranzaksiyalar
    import_txns = Transaction.objects.filter(
        branch=branch,
        metadata__source='student_import'
    )
    print(f"   ✓ Import tranzaksiyalari: {import_txns.count()}")
    
    if import_txns.exists():
        total_amount = sum(t.amount for t in import_txns)
        print(f"   ✓ Jami import summa: {total_amount:,} so'm")
        
        for txn in import_txns[:3]:
            print(f"     - {txn.student_profile}: {txn.amount:,} so'm")
    
    # Student balanslar
    test_phones = ['+998909999991', '+998909999992', '+998909999993']
    print(f"\n   Student balanslar:")
    for phone in test_phones:
        user = User.objects.filter(phone_number=phone).first()
        if user:
            profile = StudentProfile.objects.filter(
                user_branch__user=user,
                user_branch__branch=branch
            ).first()
            if profile:
                balance = StudentBalance.objects.filter(student_profile=profile).first()
                balance_amount = balance.balance if balance else 0
                print(f"     - {profile}: {balance_amount:,} so'm")
            else:
                print(f"     - {phone}: Profile topilmadi")
        else:
            print(f"     - {phone}: User topilmadi")
    
    print("\n" + "="*80)
    print("TEST TUGADI ✓")
    print("="*80)


if __name__ == '__main__':
    main()
