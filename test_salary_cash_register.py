"""
Test script to verify salary payment updates cash register balance.

Test quyidagilarni tekshiradi:
1. Xodim balansini o'zgartirish (create_cash_transaction=True)
2. Kassa balansidan pul chiqariladi
3. Xodim balansi yangilanadi
4. CashTransaction yaratiladi
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from datetime import date
from apps.branch.models import Branch, BranchMembership
from apps.school.finance.models import CashRegister
from apps.branch.services import SalaryPaymentService
from apps.branch.choices import TransactionType

def test_salary_payment_with_cash():
    """Test salary payment with cash register transaction."""
    
    print("\n" + "=" * 60)
    print("XODIM MAOSH TO'LOVI TESTI (KASSA BILAN)")
    print("=" * 60)
    
    # 1. Filial va xodim
    branch = Branch.objects.filter(deleted_at__isnull=True).first()
    if not branch:
        print("❌ Filial topilmadi!")
        return False
    
    staff = BranchMembership.objects.filter(
        branch=branch,
        deleted_at__isnull=True
    ).exclude(role='student').first()
    
    if not staff:
        # Xodim yaratish
        from django.contrib.auth import get_user_model
        from apps.branch.models import BranchRole
        
        User = get_user_model()
        test_user = User.objects.create_user(
            phone_number="+998901234888",
            first_name="Test",
            last_name="Xodim",
            password="testpass123"
        )
        
        staff = BranchMembership.objects.create(
            user=test_user,
            branch=branch,
            role=BranchRole.TEACHER,
            balance=2_000_000  # Boshlang'ich balans
        )
        print(f"✓ Yangi xodim yaratildi: {staff.user.get_full_name()}")
    
    # Xodim balansiga pul qo'shish (agar kamida)
    if staff.balance < 1_000_000:
        staff.balance = 2_000_000
        staff.save()
    
    print(f"✓ Xodim: {staff.user.get_full_name()}")
    print(f"✓ Xodim balansi: {staff.balance:,} so'm")
    
    # 2. Kassa
    cash_register = CashRegister.objects.filter(
        branch=branch,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not cash_register:
        cash_register = CashRegister.objects.create(
            branch=branch,
            name="Test kassa (maosh)",
            balance=5_000_000  # Yetarli mablag'
        )
    elif cash_register.balance < 1_000_000:
        cash_register.balance = 5_000_000
        cash_register.save()
    
    initial_cash_balance = cash_register.balance
    initial_staff_balance = staff.balance
    
    print(f"✓ Kassa: {cash_register.name}")
    print(f"✓ Kassa balansi: {initial_cash_balance:,} so'm")
    
    # 3. Maosh to'lovi (kassa bilan)
    salary_amount = 800_000
    
    print(f"\nMaosh to'lovi: {salary_amount:,} so'm (kassa bilan)")
    
    try:
        result = SalaryPaymentService.change_balance(
            staff=staff,
            transaction_type=TransactionType.DEDUCTION,
            amount=salary_amount,
            description="Test maosh to'lovi",
            cash_register_id=str(cash_register.id),
            create_cash_transaction=True,
            payment_method='cash',
            reference='TEST-SALARY-001',
            processed_by=None
        )
        
        print(f"✓ Balance transaction yaratildi: {result['balance_transaction'].id}")
        if result['cash_transaction']:
            print(f"✓ Cash transaction yaratildi: {result['cash_transaction'].id}")
        else:
            print("❌ Cash transaction yaratilmadi!")
    
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False
    
    # 4. Natijalarni tekshirish
    staff.refresh_from_db()
    cash_register.refresh_from_db()
    
    new_staff_balance = staff.balance
    new_cash_balance = cash_register.balance
    
    staff_diff = initial_staff_balance - new_staff_balance
    cash_diff = initial_cash_balance - new_cash_balance
    
    print(f"\n{'='*60}")
    print("XODIM BALANSI:")
    print(f"{'='*60}")
    print(f"Boshlang'ich: {initial_staff_balance:,} so'm")
    print(f"Yangi balans:  {new_staff_balance:,} so'm")
    print(f"Farq:          -{staff_diff:,} so'm")
    print(f"Kutilgan:      -{salary_amount:,} so'm")
    
    staff_ok = (staff_diff == salary_amount)
    if staff_ok:
        print("✅ Xodim balansi to'g'ri!")
    else:
        print("❌ Xodim balansi noto'g'ri!")
    
    print(f"\n{'='*60}")
    print("KASSA BALANSI:")
    print(f"{'='*60}")
    print(f"Boshlang'ich: {initial_cash_balance:,} so'm")
    print(f"Yangi balans:  {new_cash_balance:,} so'm")
    print(f"Farq:          -{cash_diff:,} so'm")
    print(f"Kutilgan:      -{salary_amount:,} so'm")
    
    cash_ok = (cash_diff == salary_amount)
    if cash_ok:
        print("✅ Kassa balansi to'g'ri!")
    else:
        print("❌ Kassa balansi noto'g'ri!")
    
    return staff_ok and cash_ok


if __name__ == '__main__':
    print("\n" + "🔥" * 30)
    print("XODIM MAOSH TO'LOVI TEST")
    print("🔥" * 30)
    
    success = test_salary_payment_with_cash()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST MUVAFFAQIYATLI O'TDI! 🎉")
    else:
        print("❌ TEST MUVAFFAQIYATSIZ! ❌")
    print("=" * 60)
