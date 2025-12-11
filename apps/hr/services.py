"""Balance service for atomic balance operations.

Ensures all balance changes are:
- Atomic (using select_for_update)
- Tracked (creates BalanceTransaction)
- Consistent (previous_balance + amount = new_balance)
"""

from django.db import transaction
from decimal import Decimal
from typing import Optional
from apps.hr.models import StaffProfile, BalanceTransaction, SalaryPayment
from apps.hr.choices import TransactionType


class BalanceService:
    """Service for managing staff balance transactions atomically."""
    
    @staticmethod
    @transaction.atomic
    def apply_transaction(
        staff: StaffProfile,
        transaction_type: str,
        amount: int,
        description: str,
        reference: str = '',
        processed_by=None,
        salary_payment: Optional[SalaryPayment] = None,
    ) -> BalanceTransaction:
        """
        Apply a balance transaction atomically.
        
        Args:
            staff: StaffProfile to update
            transaction_type: Type from TransactionType choices
            amount: Amount in som (positive integer)
            description: Transaction description
            reference: Optional reference (invoice #, etc.)
            processed_by: User who processed the transaction
            salary_payment: Optional linked SalaryPayment
            
        Returns:
            Created BalanceTransaction instance
            
        Raises:
            ValueError: If amount is negative or invalid type
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Lock the staff profile row
        staff = StaffProfile.objects.select_for_update().get(pk=staff.pk)
        
        previous_balance = staff.current_balance
        
        # Calculate new balance based on transaction type
        if transaction_type in [
            TransactionType.DEPOSIT,
            TransactionType.SALARY,
            TransactionType.BONUS,
        ]:
            # Credit transactions increase balance
            new_balance = previous_balance + amount
        elif transaction_type in [
            TransactionType.WITHDRAWAL,
            TransactionType.FINE,
        ]:
            # Debit transactions decrease balance
            new_balance = previous_balance - amount
        elif transaction_type == TransactionType.ADJUSTMENT:
            # Adjustment can be positive or negative based on context
            # For simplicity, treat as credit
            new_balance = previous_balance + amount
        elif transaction_type == TransactionType.ADVANCE:
            # Advance decreases balance (it's a pre-payment)
            new_balance = previous_balance - amount
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        
        # Create transaction record
        txn = BalanceTransaction.objects.create(
            staff=staff,
            transaction_type=transaction_type,
            amount=amount,
            previous_balance=previous_balance,
            new_balance=new_balance,
            reference=reference,
            description=description,
            processed_by=processed_by,
            salary_payment=salary_payment,
        )
        
        # Update staff balance
        staff.current_balance = new_balance
        staff.save(update_fields=['current_balance', 'updated_at'])
        
        return txn
    
    @staticmethod
    def get_balance_summary(staff: StaffProfile) -> dict:
        """
        Get balance summary for a staff member.
        
        Returns:
            Dict with current balance, total credits, total debits
        """
        from django.db.models import Sum, Q
        
        transactions = BalanceTransaction.objects.filter(
            staff=staff,
            deleted_at__isnull=True
        )
        
        credit_types = [
            TransactionType.DEPOSIT,
            TransactionType.SALARY,
            TransactionType.BONUS,
        ]
        debit_types = [
            TransactionType.WITHDRAWAL,
            TransactionType.FINE,
            TransactionType.ADVANCE,
        ]
        
        total_credits = transactions.filter(
            transaction_type__in=credit_types
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_debits = transactions.filter(
            transaction_type__in=debit_types
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'current_balance': staff.current_balance,
            'total_credits': total_credits,
            'total_debits': total_debits,
            'net': total_credits - total_debits,
        }
