"""
Test script to verify payment creation updates cash register balance.

Test quyidagilarni tekshiradi:
1. To'lov yaratilganda kassa balansiga pul qo'shiladi
2. Tranzaksiya completed statusda bo'ladi
3. O'quvchi balansi ham yangilanadi
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from apps.branch.models import Branch
from auth.profiles.models import StudentProfile
from apps.school.finance.models import (
    CashRegister, Transaction, Payment, StudentBalance, SubscriptionPlan,
    TransactionType, TransactionStatus, PaymentMethod
)

def test_payment_cash_register():
    """Test payment creation and cash register balance update."""
    
    print("=" * 60)
    print("PAYMENT CASH REGISTER BALANCE TEST")
    print("=" * 60)
    
    # 1. Filialni topish
    branch = Branch.objects.filter(deleted_at__isnull=True).first()
    if not branch:
        print("❌ Filial topilmadi!")
        return
    
    print(f"✓ Filial: {branch.name}")
    
    # 2. Kassani topish yoki yaratish
    cash_register = CashRegister.objects.filter(
        branch=branch,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not cash_register:
        cash_register = CashRegister.objects.create(
            branch=branch,
            name="Test kassa",
            balance=0
        )
        print(f"✓ Yangi kassa yaratildi: {cash_register.name}")
    else:
        print(f"✓ Kassa topildi: {cash_register.name}")
    
    initial_balance = cash_register.balance
    print(f"✓ Boshlang'ich balans: {initial_balance:,} so'm")
    
    # 3. O'quvchini topish yoki yaratish
    student = StudentProfile.objects.filter(
        user_branch__branch=branch,
        deleted_at__isnull=True
    ).first()
    
    if not student:
        # Yangi o'quvchi yaratish
        from django.contrib.auth import get_user_model
        from apps.branch.models import BranchMembership, BranchRole
        from auth.profiles.models import StudentStatus
        
        User = get_user_model()
        
        # User yaratish
        test_user = User.objects.create_user(
            phone_number="+998901234999",
            first_name="Test",
            last_name="O'quvchi",
            password="testpass123"
        )
        
        # BranchMembership yaratish
        membership = BranchMembership.objects.create(
            user=test_user,
            branch=branch,
            role=BranchRole.STUDENT
        )
        
        # StudentProfile get_or_create (signal yaratgan bo'lishi mumkin)
        student, created = StudentProfile.objects.get_or_create(
            user_branch=membership,
            defaults={
                'middle_name': "Testovich",
                'gender': "male",
                'status': StudentStatus.ACTIVE
            }
        )
        print(f"✓ Yangi o'quvchi {'yaratildi' if created else 'topildi'}: {student.full_name} ({student.personal_number})")
    else:
        print(f"✓ O'quvchi topildi: {student.full_name} ({student.personal_number})")
    
    # 4. Subscription plan topish
    subscription_plan = SubscriptionPlan.objects.filter(
        branch=branch,
        is_active=True,
        deleted_at__isnull=True
    ).first()
    
    if not subscription_plan:
        print("⚠ Subscription plan topilmadi, 500,000 so'm ishlatamiz")
        subscription_plan = None
        payment_amount = 500_000
    else:
        print(f"✓ Subscription plan: {subscription_plan.name} - {subscription_plan.price:,} so'm")
        payment_amount = subscription_plan.price
    
    # 5. O'quvchining boshlang'ich balansini olish
    student_balance, _ = StudentBalance.objects.get_or_create(
        student_profile=student
    )
    initial_student_balance = student_balance.balance
    print(f"✓ O'quvchi boshlang'ich balansi: {initial_student_balance:,} so'm")
    
    # 6. To'lov yaratish (Serializer orqali)
    from apps.school.finance.serializers import PaymentCreateSerializer
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    today = date.today()
    next_month = today + relativedelta(months=1)
    
    payment_data = {
        'student_profile': student.id,
        'branch': branch.id,
        'subscription_plan': subscription_plan.id if subscription_plan else None,
        'base_amount': payment_amount,
        'payment_method': PaymentMethod.CASH,
        'payment_date': timezone.now(),
        'period_start': today,
        'period_end': next_month,
        'period': 'monthly',
        'cash_register': str(cash_register.id),
        'notes': 'Test to\'lov - kassa balansi testi'
    }
    
    print("\n" + "-" * 60)
    print("TO'LOV YARATISH...")
    print("-" * 60)
    
    serializer = PaymentCreateSerializer(data=payment_data)
    
    if not serializer.is_valid():
        print("❌ Serializer validatsiyadan o'tmadi:")
        print(serializer.errors)
        return
    
    payment = serializer.save()
    print(f"✓ To'lov yaratildi: {payment.id}")
    print(f"✓ To'lov summasi: {payment.final_amount:,} so'm")
    
    # 7. Tranzaksiyani tekshirish
    transaction = payment.transaction
    print(f"✓ Tranzaksiya yaratildi: {transaction.id}")
    print(f"✓ Tranzaksiya status: {transaction.status}")
    print(f"✓ Tranzaksiya turi: {transaction.transaction_type}")
    print(f"✓ Tranzaksiya summasi: {transaction.amount:,} so'm")
    
    # 8. Kassa balansini tekshirish
    cash_register.refresh_from_db()
    new_balance = cash_register.balance
    balance_diff = new_balance - initial_balance
    
    print("\n" + "-" * 60)
    print("KASSA BALANSI NATIJASI")
    print("-" * 60)
    print(f"Boshlang'ich balans: {initial_balance:,} so'm")
    print(f"Yangi balans:        {new_balance:,} so'm")
    print(f"Farq:                {balance_diff:,} so'm")
    print(f"Kutilgan:            +{payment_amount:,} so'm")
    
    if balance_diff == payment_amount:
        print("✅ KASSA BALANSI TO'G'RI YANGILANDI!")
    else:
        print("❌ MUAMMO: Kassa balansi noto'g'ri yangilandi!")
        print(f"   Kutilgan: +{payment_amount:,} so'm")
        print(f"   Haqiqiy:  +{balance_diff:,} so'm")
    
    # 9. O'quvchi balansini tekshirish
    student_balance.refresh_from_db()
    new_student_balance = student_balance.balance
    student_balance_diff = new_student_balance - initial_student_balance
    
    print("\n" + "-" * 60)
    print("O'QUVCHI BALANSI NATIJASI")
    print("-" * 60)
    print(f"Boshlang'ich balans: {initial_student_balance:,} so'm")
    print(f"Yangi balans:        {new_student_balance:,} so'm")
    print(f"Farq:                {student_balance_diff:,} so'm")
    print(f"Kutilgan:            +{payment_amount:,} so'm")
    
    if student_balance_diff == payment_amount:
        print("✅ O'QUVCHI BALANSI TO'G'RI YANGILANDI!")
    else:
        print("❌ MUAMMO: O'quvchi balansi noto'g'ri yangilandi!")
    
    # 10. Tranzaksiya statusini tekshirish
    print("\n" + "-" * 60)
    print("TRANZAKSIYA STATUSINI TEKSHIRISH")
    print("-" * 60)
    
    if transaction.status == TransactionStatus.COMPLETED:
        print("✅ Tranzaksiya COMPLETED statusda!")
    else:
        print(f"❌ MUAMMO: Tranzaksiya {transaction.status} statusda!")
    
    print("\n" + "=" * 60)
    print("TEST YAKUNLANDI")
    print("=" * 60)
    
    # Xulosa
    all_ok = (
        balance_diff == payment_amount and
        student_balance_diff == payment_amount and
        transaction.status == TransactionStatus.COMPLETED
    )
    
    if all_ok:
        print("✅✅✅ BARCHA TESTLAR MUVAFFAQIYATLI O'TDI! ✅✅✅")
    else:
        print("❌❌❌ BA'ZI TESTLAR MUVAFFAQIYATSIZ! ❌❌❌")

if __name__ == '__main__':
    test_payment_cash_register()
