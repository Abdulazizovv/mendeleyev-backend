"""
Student import tranzaksiyalarini test qilish skripti
"""

import django
import os
import sys

# Django setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.school.finance.models import Transaction, StudentBalance, CashRegister
from auth.profiles.models import StudentProfile
from apps.branch.models import Branch
from django.db.models import Sum


def test_import_transactions():
    """Import qilingandan keyin tranzaksiyalarni tekshirish"""
    
    print("\n" + "="*80)
    print("STUDENT IMPORT TRANZAKSIYA TESTI")
    print("="*80)
    
    # Test branch ID (sizning branch ID'ingiz)
    branch_id = 'e62d7159-d9d6-4913-ac49-c90fa8b4b79c'
    
    try:
        branch = Branch.objects.get(id=branch_id)
        print(f"\n✓ Branch topildi: {branch.name}")
    except Branch.DoesNotExist:
        print(f"\n✗ Branch topilmadi: {branch_id}")
        return
    
    # 1. Studentlar sonini tekshirish
    students_count = StudentProfile.objects.filter(
        user_branch__branch_id=branch_id,
        deleted_at__isnull=True
    ).count()
    print(f"\n✓ Jami studentlar: {students_count}")
    
    # 2. Import tranzaksiyalarini tekshirish
    import_transactions = Transaction.objects.filter(
        branch=branch,
        student_profile__isnull=False,
        description__icontains="Import: Boshlang'ich balans",
        deleted_at__isnull=True
    )
    
    print(f"\n✓ Import tranzaksiyalari: {import_transactions.count()}")
    
    if import_transactions.exists():
        total_import_amount = import_transactions.aggregate(total=Sum('amount'))['total'] or 0
        print(f"  - Jami summa: {total_import_amount:,} so'm")
        
        # So'ngi 5 ta tranzaksiya
        print("\n  So'ngi 5 ta import tranzaksiyasi:")
        for trans in import_transactions.order_by('-created_at')[:5]:
            student_name = trans.student_profile.user_branch.user.get_full_name()
            print(f"    • {student_name}: {trans.amount:,} so'm (ID: {trans.id})")
    else:
        print("  ⚠ Hech qanday import tranzaksiyasi topilmadi!")
    
    # 3. StudentBalance'larni tekshirish
    student_balances = StudentBalance.objects.filter(
        student_profile__user_branch__branch_id=branch_id,
        deleted_at__isnull=True
    )
    
    print(f"\n✓ StudentBalance yozuvlari: {student_balances.count()}")
    
    balances_with_amount = student_balances.filter(balance__gt=0)
    if balances_with_amount.exists():
        total_balance = student_balances.aggregate(total=Sum('balance'))['total'] or 0
        print(f"  - Jami balans: {total_balance:,} so'm")
        print(f"  - Balansi bor studentlar: {balances_with_amount.count()}")
        
        # So'ngi 5 ta balans
        print("\n  So'ngi 5 ta student balansi:")
        for sb in balances_with_amount.order_by('-balance')[:5]:
            student_name = sb.student_profile.user_branch.user.get_full_name()
            print(f"    • {student_name}: {sb.balance:,} so'm")
    else:
        print("  ℹ Hamma studentlarning balansi 0")
    
    # 4. CashRegister holatini tekshirish
    cash_registers = CashRegister.objects.filter(
        branch=branch,
        deleted_at__isnull=True
    )
    
    print(f"\n✓ Kassa registrlari: {cash_registers.count()}")
    for cr in cash_registers:
        print(f"  - {cr.name}: {cr.balance:,} so'm")
    
    # 5. Tranzaksiya va balans mos kelishini tekshirish
    print("\n" + "="*80)
    print("BALANS VALIDATSIYASI")
    print("="*80)
    
    for student_balance in student_balances.filter(balance__gt=0)[:10]:
        student_name = student_balance.student_profile.user_branch.user.get_full_name()
        
        # Ushbu student uchun barcha tranzaksiyalar
        student_transactions = Transaction.objects.filter(
            student_profile=student_balance.student_profile,
            status='completed',
            deleted_at__isnull=True
        )
        
        # Income va expense hisoblash
        income = student_transactions.filter(
            transaction_type__in=['income', 'payment']
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expense = student_transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        calculated_balance = income - expense
        actual_balance = student_balance.balance
        
        status = "✓" if calculated_balance == actual_balance else "✗"
        print(f"\n{status} {student_name}")
        print(f"  - Hisoblangan: {calculated_balance:,} so'm")
        print(f"  - Haqiqiy:     {actual_balance:,} so'm")
        
        if calculated_balance != actual_balance:
            print(f"  ⚠ FARQ: {abs(calculated_balance - actual_balance):,} so'm")
    
    print("\n" + "="*80)
    print("TEST TUGADI")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_import_transactions()
