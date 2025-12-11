"""HR signals for automatic profile management."""

from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.branch.models import BranchMembership


@receiver(post_save, sender='hr.SalaryPayment')
def create_balance_transaction_on_payment(sender, instance, created, **kwargs):
    """
    Automatically create a balance transaction when salary payment is marked as paid.
    
    This keeps balance and salary payments in sync.
    """
    from apps.hr.models import SalaryPayment
    from apps.hr.services import BalanceService
    from apps.hr.choices import TransactionType, PaymentStatus
    
    if instance.status == PaymentStatus.PAID:
        # Check if transaction already exists
        if not instance.transactions.exists():
            BalanceService.apply_transaction(
                staff=instance.staff,
                transaction_type=TransactionType.SALARY,
                amount=instance.amount,
                description=f"Maosh to'lovi - {instance.month.strftime('%B %Y')}",
                reference=instance.reference_number or f"SALARY-{instance.id}",
                processed_by=instance.processed_by,
                salary_payment=instance,
            )
