"""
Balans bilan test student import qilish
"""

import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.school.students.tasks import import_students_task
import io
from openpyxl import Workbook


def create_test_excel_with_balance():
    """Balansli test Excel fayl yaratish"""
    wb = Workbook()
    ws = wb.active
    
    # Headers
    ws.append([
        'Shartnoma',
        'FIO',
        'Balans',
        'Sinf',
        'Guruh',
        'Telefon',
        'Sinf Rahbari',
        'Jinsi',
        'Tug\'ilgan kuni',
        'Manzil'
    ])
    
    # Test students with different balances
    test_students = [
        ['TEST-001', 'Testov Test Testovich', 500000, '10-A', '-', '+998901234567', '-', 'male', '2010-01-15', 'Toshkent sh.'],
        ['TEST-002', 'Testova Testa Testovna', 300000, '10-A', '-', '+998901234568', '-', 'female', '2010-02-20', 'Toshkent sh.'],
        ['TEST-003', 'Sinov Ali Valiovich', 0, '10-B', '-', '+998901234569', '-', 'male', '2010-03-25', 'Toshkent sh.'],
        ['TEST-004', 'Sinova Olima Karimovna', -100000, '10-B', '-', '+998901234570', '-', 'female', '2010-04-30', 'Toshkent sh.'],
        ['TEST-005', 'Imtihon Sardor Shavkatovich', 1000000, '11-A', '-', '+998901234571', '-', 'male', '2009-05-10', 'Toshkent sh.'],
    ]
    
    for student in test_students:
        ws.append(student)
    
    # Save to BytesIO
    excel_bytes = io.BytesIO()
    wb.save(excel_bytes)
    excel_bytes.seek(0)
    
    return excel_bytes.read()


def main():
    branch_id = 'e62d7159-d9d6-4913-ac49-c90fa8b4b79c'
    
    print("\n" + "="*80)
    print("BALANSLI STUDENTLARNI IMPORT TEST")
    print("="*80)
    
    # 1. Excel yaratish
    print("\n1. Test Excel fayl yaratish...")
    excel_content = create_test_excel_with_balance()
    print(f"   ✓ Excel yaratildi ({len(excel_content)} bytes)")
    
    # 2. Dry run
    print("\n2. Dry run (validatsiya)...")
    dry_run_result = import_students_task(excel_content, branch_id, dry_run=True)
    print(f"   ✓ Total: {dry_run_result['total']}")
    print(f"   ✓ Will create: {dry_run_result['success']}")
    print(f"   ✓ Already exists: {dry_run_result['skipped']}")
    
    if dry_run_result['errors']:
        print("\n   Xatolar:")
        for error in dry_run_result['errors'][:3]:
            print(f"     - Row {error['row']}: {error['error']}")
    
    # 3. Haqiqiy import
    print("\n3. Haqiqiy import...")
    result = import_students_task(excel_content, branch_id, dry_run=False)
    print(f"   ✓ Total: {result['total']}")
    print(f"   ✓ Created: {result['success']}")
    print(f"   ✓ Skipped: {result['skipped']}")
    print(f"   ✓ Failed: {result['failed']}")
    
    if result['errors']:
        print("\n   Xatolar:")
        for error in result['errors'][:3]:
            print(f"     - Row {error.get('row', '?')}: {error['error']}")
    
    # 4. Tranzaksiyalarni tekshirish
    print("\n4. Tranzaksiyalarni tekshirish...")
    from apps.school.finance.models import Transaction
    from django.db.models import Sum
    
    import_transactions = Transaction.objects.filter(
        branch_id=branch_id,
        description__icontains="Import: Boshlang'ich balans",
        deleted_at__isnull=True
    )
    
    print(f"   ✓ Import tranzaksiyalari: {import_transactions.count()}")
    
    if import_transactions.exists():
        total_amount = import_transactions.aggregate(total=Sum('amount'))['total'] or 0
        print(f"   ✓ Jami summa: {total_amount:,} so'm")
        
        print("\n   Tranzaksiyalar:")
        for trans in import_transactions:
            student = trans.student_profile.user_branch.user.get_full_name()
            print(f"     - {student}: {trans.amount:,} so'm")
    
    # 5. Student balanslarni tekshirish
    print("\n5. Student balanslarni tekshirish...")
    from apps.school.finance.models import StudentBalance
    
    balances = StudentBalance.objects.filter(
        student_profile__user_branch__branch_id=branch_id,
        deleted_at__isnull=True
    )
    
    print(f"   ✓ StudentBalance yozuvlari: {balances.count()}")
    
    for balance in balances:
        student = balance.student_profile.user_branch.user.get_full_name()
        print(f"     - {student}: {balance.balance:,} so'm")
    
    print("\n" + "="*80)
    print("TEST TUGADI ✓")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
