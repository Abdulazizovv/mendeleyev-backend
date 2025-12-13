"""Balance service for atomic balance operations.

Ensures all balance changes are:
- Atomic (using select_for_update)
- Tracked (creates BalanceTransaction)
- Consistent (previous_balance + amount = new_balance)
"""

from django.db import transaction
from typing import Optional
import uuid
from apps.branch.models import BranchMembership, BalanceTransaction, SalaryPayment
from apps.branch.choices import TransactionType


class BalanceService:
    """Service for managing staff balance transactions atomically."""
    
    @staticmethod
    @transaction.atomic
    def apply_transaction(
        membership: BranchMembership,
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
            membership: BranchMembership to update
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
        
        # Lock the membership row for update
        membership = BranchMembership.objects.select_for_update().get(pk=membership.pk)
        
        previous_balance = membership.balance
        
        # Determine if this is a credit or debit based on transaction type
        if transaction_type in [TransactionType.DEDUCTION, TransactionType.FINE]:
            # Debit - subtract from balance
            new_balance = previous_balance - amount
        else:
            # Credit - add to balance (SALARY, BONUS, ADVANCE, ADJUSTMENT, OTHER)
            new_balance = previous_balance + amount
        
        # Update membership balance
        membership.balance = new_balance
        membership.save(update_fields=['balance', 'updated_at'])
        
        # Create transaction record
        balance_transaction = BalanceTransaction.objects.create(
            membership=membership,
            transaction_type=transaction_type,
            amount=amount,
            previous_balance=previous_balance,
            new_balance=new_balance,
            reference=reference,
            description=description,
            salary_payment=salary_payment,
            processed_by=processed_by
        )
        
        return balance_transaction
    
    @staticmethod
    @transaction.atomic
    def add_salary(
        membership: BranchMembership,
        amount: int,
        description: str = '',
        reference: str = '',
        processed_by=None,
        salary_payment: Optional[SalaryPayment] = None,
    ) -> BalanceTransaction:
        """
        Add salary to membership balance.
        
        Convenience method for salary transactions.
        """
        if not description:
            description = f"Maosh to'lovi - {amount:_} so'm"
        
        return BalanceService.apply_transaction(
            membership=membership,
            transaction_type=TransactionType.SALARY,
            amount=amount,
            description=description,
            reference=reference,
            processed_by=processed_by,
            salary_payment=salary_payment
        )
    
    @staticmethod
    @transaction.atomic
    def add_bonus(
        membership: BranchMembership,
        amount: int,
        description: str,
        reference: str = '',
        processed_by=None,
    ) -> BalanceTransaction:
        """
        Add bonus to membership balance.
        
        Convenience method for bonus transactions.
        """
        return BalanceService.apply_transaction(
            membership=membership,
            transaction_type=TransactionType.BONUS,
            amount=amount,
            description=description,
            reference=reference,
            processed_by=processed_by
        )
    
    @staticmethod
    @transaction.atomic
    def apply_deduction(
        membership: BranchMembership,
        amount: int,
        description: str,
        reference: str = '',
        processed_by=None,
    ) -> BalanceTransaction:
        """
        Apply deduction to membership balance.
        
        Convenience method for deduction transactions.
        """
        return BalanceService.apply_transaction(
            membership=membership,
            transaction_type=TransactionType.DEDUCTION,
            amount=amount,
            description=description,
            reference=reference,
            processed_by=processed_by
        )
    
    @staticmethod
    @transaction.atomic
    def give_advance(
        membership: BranchMembership,
        amount: int,
        description: str = '',
        reference: str = '',
        processed_by=None,
    ) -> BalanceTransaction:
        """
        Give advance payment to membership.
        
        Convenience method for advance transactions.
        """
        if not description:
            description = f"Avans to'lovi - {amount:_} so'm"
        
        return BalanceService.apply_transaction(
            membership=membership,
            transaction_type=TransactionType.ADVANCE,
            amount=amount,
            description=description,
            reference=reference,
            processed_by=processed_by
        )
    
    @staticmethod
    @transaction.atomic
    def apply_fine(
        membership: BranchMembership,
        amount: int,
        description: str,
        reference: str = '',
        processed_by=None,
    ) -> BalanceTransaction:
        """
        Apply fine to membership balance.
        
        Convenience method for fine transactions.
        """
        return BalanceService.apply_transaction(
            membership=membership,
            transaction_type=TransactionType.FINE,
            amount=amount,
            description=description,
            reference=reference,
            processed_by=processed_by
        )
    
    @staticmethod
    def get_balance(membership_id: uuid.UUID) -> int:
        """
        Get current balance for a membership.
        
        Args:
            membership_id: UUID of the membership
            
        Returns:
            Current balance in som
        """
        membership = BranchMembership.objects.get(pk=membership_id)
        return membership.balance
    
    @staticmethod
    def get_transaction_history(
        membership_id: uuid.UUID,
        transaction_type: Optional[str] = None,
        limit: int = 100
    ):
        """
        Get transaction history for a membership.
        
        Args:
            membership_id: UUID of the membership
            transaction_type: Optional filter by transaction type
            limit: Maximum number of records to return
            
        Returns:
            QuerySet of BalanceTransaction objects
        """
        qs = BalanceTransaction.objects.filter(
            membership_id=membership_id
        ).select_related('membership', 'membership__user', 'processed_by')
        
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        
        return qs[:limit]
