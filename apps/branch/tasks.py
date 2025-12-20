"""Celery tasks for branch app - staff salary calculations."""

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from datetime import date
import calendar
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def calculate_daily_salary_accrual(self):
    """
    Har kuni xodimlarning oylik maoshlarini kunlik hisoblash.
    
    Masalan: Oylik maosh 3,000,000 so'm
    - 30 kunlik oyda: 3,000,000 / 30 = 100,000 so'm kunlik
    - 31 kunlik oyda: 3,000,000 / 31 = 96,774 so'm kunlik
    
    Bu task har kuni soat 00:00 da ishga tushadi.
    """
    from apps.branch.models import BranchMembership, BalanceTransaction
    from apps.branch.choices import TransactionType
    
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    # Faqat faol xodimlar va oylik maoshli xodimlarni olish
    active_staff = BranchMembership.objects.filter(
        termination_date__isnull=True,
        deleted_at__isnull=True,
        monthly_salary__gt=0,
        salary_type='monthly'
    ).select_related('user', 'branch')
    
    created_count = 0
    total_amount = 0
    
    with transaction.atomic():
        for staff in active_staff:
            # Kunlik maoshni hisoblash
            daily_salary = staff.monthly_salary // days_in_month
            
            if daily_salary <= 0:
                continue
            
            # Balansni yangilash
            previous_balance = staff.balance
            staff.balance += daily_salary
            new_balance = staff.balance
            staff.save(update_fields=['balance', 'updated_at'])
            
            # Tranzaksiya yaratish
            BalanceTransaction.objects.create(
                membership=staff,
                transaction_type=TransactionType.SALARY_ACCRUAL,
                amount=daily_salary,
                previous_balance=previous_balance,
                new_balance=new_balance,
                description=f"Kunlik maosh hisoblash: {today.strftime('%d.%m.%Y')} ({today.day}/{days_in_month} kun)",
                reference=f"DAILY-{today.strftime('%Y%m%d')}",
                processed_by=None  # Avtomatik system tomonidan
            )
            
            created_count += 1
            total_amount += daily_salary
            
            logger.info(
                f"Daily salary accrued: {staff.user.get_full_name()} - "
                f"{daily_salary:,} so'm ({staff.branch.name})"
            )
    
    logger.info(
        f"Daily salary accrual completed: {created_count} staff members, "
        f"total amount: {total_amount:,} so'm"
    )
    
    return {
        'date': today.isoformat(),
        'staff_count': created_count,
        'total_amount': total_amount,
        'days_in_month': days_in_month
    }


@shared_task(bind=True)
def recalculate_staff_balances(self, branch_id=None):
    """
    Xodimlarning balanslarini qayta hisoblash.
    
    Bu task ma'lumotlar bazasida xatolik bo'lsa yoki 
    balanslarni qayta hisoblash kerak bo'lganda ishlatiladi.
    """
    from apps.branch.models import BranchMembership, BalanceTransaction
    
    queryset = BranchMembership.objects.filter(deleted_at__isnull=True)
    
    if branch_id:
        queryset = queryset.filter(branch_id=branch_id)
    
    updated_count = 0
    
    with transaction.atomic():
        for staff in queryset.select_related('user'):
            # Barcha tranzaksiyalarni olish
            transactions = BalanceTransaction.objects.filter(
                membership=staff
            ).order_by('created_at')
            
            # Balansni qayta hisoblash
            calculated_balance = 0
            for trans in transactions:
                if trans.transaction_type in ['salary', 'bonus']:
                    calculated_balance += trans.amount
                elif trans.transaction_type in ['deduction', 'advance', 'fine']:
                    calculated_balance -= trans.amount
            
            # Agar farq bo'lsa yangilash
            if staff.balance != calculated_balance:
                old_balance = staff.balance
                staff.balance = calculated_balance
                staff.save(update_fields=['balance', 'updated_at'])
                
                logger.info(
                    f"Balance recalculated: {staff.user.get_full_name()} - "
                    f"{old_balance:,} -> {calculated_balance:,} so'm"
                )
                updated_count += 1
    
    logger.info(f"Balance recalculation completed: {updated_count} staff members updated")
    
    return {
        'updated_count': updated_count,
        'branch_id': branch_id
    }
