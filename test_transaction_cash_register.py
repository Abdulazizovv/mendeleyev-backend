"""
Test script to verify transaction creation updates cash register balance.

Test quyidagilarni tekshiradi:
1. Kirim yaratilganda kassa balansiga pul qo'shiladi
2. Chiqim yaratilganda kassa balansidan pul ayiriladi
3. PENDING statusdagi tranzaksiyalar balansni o'zgartirmaydi
4. PENDING dan COMPLETED ga o'zgarganda balans yangilanadi
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from apps.branch.models import Branch
from apps.school.finance.models import (
    CashRegister, Transaction, FinanceCategory,
    TransactionType, TransactionStatus, PaymentMethod
)

def test_income_transaction():
    """Test income transaction and cash register balance update."""
    
    print("\n" + "=" * 60)
    print("KIRIM TRANZAKSIYASI TESTI")
    print("=" * 60)
    
    # 1. Filial va kassa
    branch = Branch.objects.filter(deleted_at__isnull=True).first()
    if not branch:
        print("❌ Filial topilmadi!")
        return False
    
    cash_register = CashRegister.objects.filter(
        branch=branch,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not cash_register:
        cash_register = CashRegister.objects.create(
            branch=branch,
            name="Test kassa (kirim)",
            balance=0
        )
    
    initial_balance = cash_register.balance
    print(f"✓ Kassa: {cash_register.name}")
    print(f"✓ Boshlang'ich balans: {initial_balance:,} so'm")
    
    # 2. Kirim kategoriyasi
    category = FinanceCategory.objects.filter(
        branch=branch,
        type='income',
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not category:
        category = FinanceCategory.objects.create(
            branch=branch,
            type='income',
            name="Test kirim",
            is_active=True
        )
    
    print(f"✓ Kategoriya: {category.name}")
    
    # 3. Kirim yaratish (Serializer orqali)
    from apps.school.finance.serializers import TransactionCreateSerializer
    
    income_amount = 1_000_000
    
    transaction_data = {
        'branch': branch.id,
        'cash_register': cash_register.id,
        'transaction_type': TransactionType.INCOME,
        'category': category.id,
        'amount': income_amount,
        'payment_method': PaymentMethod.CASH,
        'description': 'Test kirim - kassa balansi testi',
        'transaction_date': timezone.now(),
        'auto_approve': True  # COMPLETED qilish uchun
    }
    
    print(f"\nKirim yaratish: {income_amount:,} so'm")
    
    serializer = TransactionCreateSerializer(data=transaction_data, context={'request': None})
    
    if not serializer.is_valid():
        print("❌ Serializer validatsiyadan o'tmadi:")
        print(serializer.errors)
        return False
    
    transaction = serializer.save()
    print(f"✓ Tranzaksiya yaratildi: {transaction.id}")
    print(f"✓ Status: {transaction.status}")
    
    # 4. Kassa balansini tekshirish
    cash_register.refresh_from_db()
    new_balance = cash_register.balance
    balance_diff = new_balance - initial_balance
    
    print(f"\n{'='*60}")
    print("NATIJA:")
    print(f"{'='*60}")
    print(f"Boshlang'ich: {initial_balance:,} so'm")
    print(f"Yangi balans: {new_balance:,} so'm")
    print(f"Farq:         {balance_diff:,} so'm")
    print(f"Kutilgan:     +{income_amount:,} so'm")
    
    if balance_diff == income_amount:
        print("✅ KIRIM TO'G'RI HISOBLANDI!")
        return True
    else:
        print("❌ MUAMMO: Kassa balansi noto'g'ri!")
        return False


def test_expense_transaction():
    """Test expense transaction and cash register balance update."""
    
    print("\n" + "=" * 60)
    print("CHIQIM TRANZAKSIYASI TESTI")
    print("=" * 60)
    
    # 1. Filial va kassa
    branch = Branch.objects.filter(deleted_at__isnull=True).first()
    cash_register = CashRegister.objects.filter(
        branch=branch,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    # Kassaga pul qo'shamiz (chiqim uchun)
    if cash_register.balance < 500_000:
        cash_register.balance = 1_000_000
        cash_register.save()
    
    initial_balance = cash_register.balance
    print(f"✓ Kassa: {cash_register.name}")
    print(f"✓ Boshlang'ich balans: {initial_balance:,} so'm")
    
    # 2. Chiqim kategoriyasi
    category = FinanceCategory.objects.filter(
        branch=branch,
        type='expense',
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not category:
        category = FinanceCategory.objects.create(
            branch=branch,
            type='expense',
            name="Test chiqim",
            is_active=True
        )
    
    print(f"✓ Kategoriya: {category.name}")
    
    # 3. Chiqim yaratish
    from apps.school.finance.serializers import TransactionCreateSerializer
    
    expense_amount = 500_000
    
    transaction_data = {
        'branch': branch.id,
        'cash_register': cash_register.id,
        'transaction_type': TransactionType.EXPENSE,
        'category': category.id,
        'amount': expense_amount,
        'payment_method': PaymentMethod.CASH,
        'description': 'Test chiqim - kassa balansi testi',
        'transaction_date': timezone.now(),
        'auto_approve': True
    }
    
    print(f"\nChiqim yaratish: {expense_amount:,} so'm")
    
    serializer = TransactionCreateSerializer(data=transaction_data, context={'request': None})
    
    if not serializer.is_valid():
        print("❌ Serializer validatsiyadan o'tmadi:")
        print(serializer.errors)
        return False
    
    transaction = serializer.save()
    print(f"✓ Tranzaksiya yaratildi: {transaction.id}")
    print(f"✓ Status: {transaction.status}")
    
    # 4. Kassa balansini tekshirish
    cash_register.refresh_from_db()
    new_balance = cash_register.balance
    balance_diff = initial_balance - new_balance  # Ayrilishi kerak
    
    print(f"\n{'='*60}")
    print("NATIJA:")
    print(f"{'='*60}")
    print(f"Boshlang'ich: {initial_balance:,} so'm")
    print(f"Yangi balans: {new_balance:,} so'm")
    print(f"Farq:         -{balance_diff:,} so'm")
    print(f"Kutilgan:     -{expense_amount:,} so'm")
    
    if balance_diff == expense_amount:
        print("✅ CHIQIM TO'G'RI HISOBLANDI!")
        return True
    else:
        print("❌ MUAMMO: Kassa balansi noto'g'ri!")
        return False


def test_pending_to_completed():
    """Test PENDING to COMPLETED status change."""
    
    print("\n" + "=" * 60)
    print("PENDING -> COMPLETED TESTI")
    print("=" * 60)
    
    # 1. Filial va kassa
    branch = Branch.objects.filter(deleted_at__isnull=True).first()
    cash_register = CashRegister.objects.filter(
        branch=branch,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    initial_balance = cash_register.balance
    print(f"✓ Boshlang'ich balans: {initial_balance:,} so'm")
    
    # 2. PENDING statusda tranzaksiya yaratish
    category = FinanceCategory.objects.filter(
        branch=branch,
        type='income',
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    from apps.school.finance.serializers import TransactionCreateSerializer
    
    pending_amount = 750_000
    
    transaction_data = {
        'branch': branch.id,
        'cash_register': cash_register.id,
        'transaction_type': TransactionType.INCOME,
        'category': category.id,
        'amount': pending_amount,
        'payment_method': PaymentMethod.CASH,
        'description': 'Test PENDING tranzaksiya',
        'transaction_date': timezone.now(),
        'auto_approve': False  # PENDING
    }
    
    serializer = TransactionCreateSerializer(data=transaction_data, context={'request': None})
    
    if not serializer.is_valid():
        print("❌ Serializer validatsiyadan o'tmadi:")
        print(serializer.errors)
        return False
    
    transaction = serializer.save()
    print(f"✓ PENDING tranzaksiya yaratildi: {transaction.id}")
    
    # 3. Balans o'zgarmaganligini tekshirish
    cash_register.refresh_from_db()
    balance_after_pending = cash_register.balance
    
    if balance_after_pending == initial_balance:
        print("✅ PENDING statusda balans o'zgarmadi")
    else:
        print("❌ MUAMMO: PENDING statusda balans o'zgardi!")
        return False
    
    # 4. COMPLETED ga o'zgartirish
    print(f"\nTranzaksiyani COMPLETED ga o'zgartirish...")
    transaction.complete()
    
    # 5. Balans yangilanganligini tekshirish
    cash_register.refresh_from_db()
    new_balance = cash_register.balance
    balance_diff = new_balance - initial_balance
    
    print(f"\n{'='*60}")
    print("NATIJA:")
    print(f"{'='*60}")
    print(f"Boshlang'ich:      {initial_balance:,} so'm")
    print(f"PENDING dan keyin: {balance_after_pending:,} so'm")
    print(f"COMPLETED keyin:   {new_balance:,} so'm")
    print(f"Farq:              {balance_diff:,} so'm")
    print(f"Kutilgan:          +{pending_amount:,} so'm")
    
    if balance_diff == pending_amount:
        print("✅ PENDING -> COMPLETED O'ZGARISHI TO'G'RI!")
        return True
    else:
        print("❌ MUAMMO: Balans noto'g'ri yangilandi!")
        return False


if __name__ == '__main__':
    print("\n" + "🔥" * 30)
    print("TRANZAKSIYA KASSA BALANSI TEST SUITE")
    print("🔥" * 30)
    
    results = []
    
    # Test 1: Kirim
    results.append(("Kirim", test_income_transaction()))
    
    # Test 2: Chiqim
    results.append(("Chiqim", test_expense_transaction()))
    
    # Test 3: PENDING -> COMPLETED
    results.append(("PENDING->COMPLETED", test_pending_to_completed()))
    
    # Xulosa
    print("\n" + "=" * 60)
    print("YAKUNIY NATIJA")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 BARCHA TESTLAR MUVAFFAQIYATLI O'TDI! 🎉")
    else:
        print("\n❌ BA'ZI TESTLAR MUVAFFAQIYATSIZ! ❌")
