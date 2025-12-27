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
        if transaction_type in [TransactionType.DEDUCTION, TransactionType.FINE, TransactionType.ADVANCE, TransactionType.ADJUSTMENT]:
            # Debit - subtract from balance (actual payments to staff)
            new_balance = previous_balance - amount
        else:
            # Credit - add to balance (SALARY_ACCRUAL, BONUS, OTHER)
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
            transaction_type=TransactionType.SALARY_ACCRUAL,
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


class SalaryCalculationService:
    """Service for calculating staff salaries."""
    
    @staticmethod
    def calculate_daily_salary(monthly_salary: int, year: int, month: int) -> int:
        """
        Calculate daily salary based on monthly salary and days in month.
        
        Args:
            monthly_salary: Monthly salary amount
            year: Year
            month: Month (1-12)
            
        Returns:
            Daily salary amount
        """
        import calendar
        days_in_month = calendar.monthrange(year, month)[1]
        return monthly_salary // days_in_month
    
    @staticmethod
    def calculate_monthly_accrual(staff, year: int, month: int):
        """
        Calculate full monthly salary accrual for a staff member.
        
        Args:
            staff: BranchMembership instance
            year: Year
            month: Month (1-12)
            
        Returns:
            dict with calculation details
        """
        import calendar
        
        if staff.salary_type != 'monthly' or staff.monthly_salary <= 0:
            return {
                'success': False,
                'reason': 'Not monthly salary or zero amount'
            }
        
        days_in_month = calendar.monthrange(year, month)[1]
        daily_salary = staff.monthly_salary // days_in_month
        total_amount = daily_salary * days_in_month
        
        return {
            'success': True,
            'monthly_salary': staff.monthly_salary,
            'days_in_month': days_in_month,
            'daily_salary': daily_salary,
            'total_amount': total_amount,
            'year': year,
            'month': month
        }
    
    @staticmethod
    def calculate_prorated_salary(staff, start_date, end_date):
        """
        Calculate prorated salary for partial month.
        
        Args:
            staff: BranchMembership instance
            start_date: Start date
            end_date: End date
            
        Returns:
            dict with calculation details
        """
        import calendar
        
        if staff.salary_type != 'monthly' or staff.monthly_salary <= 0:
            return {
                'success': False,
                'reason': 'Not monthly salary or zero amount'
            }
        
        # Calculate days worked
        days_worked = (end_date - start_date).days + 1
        
        # Get days in month
        days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
        
        # Calculate prorated amount
        daily_salary = staff.monthly_salary // days_in_month
        prorated_amount = daily_salary * days_worked
        
        return {
            'success': True,
            'monthly_salary': staff.monthly_salary,
            'days_in_month': days_in_month,
            'days_worked': days_worked,
            'daily_salary': daily_salary,
            'prorated_amount': prorated_amount,
            'start_date': start_date,
            'end_date': end_date
        }


class SalaryPaymentService:
    """Service for processing salary payments and balance changes."""
    
    @staticmethod
    @transaction.atomic
    def change_balance(
        staff,
        transaction_type: str,
        amount: int,
        description: str,
        cash_register_id = None,
        create_cash_transaction: bool = False,
        payment_method: str = 'cash',
        reference: str = '',
        processed_by = None
    ):
        """
        Change staff balance with optional cash register transaction.
        
        Args:
            staff: BranchMembership instance
            transaction_type: Type from TransactionType choices
            amount: Amount in som (positive integer)
            description: Transaction description
            cash_register_id: Optional CashRegister UUID for cash transaction
            create_cash_transaction: Whether to create cash register transaction
            payment_method: Payment method (cash, bank_transfer, etc)
            reference: Optional reference
            processed_by: User who processed the transaction
            
        Returns:
            dict with balance_transaction and optional cash_transaction
            
        Raises:
            ValueError: If amount is invalid or cash register required but not provided
        """
        from apps.school.finance.models import Transaction as CashTransaction
        from apps.school.finance.models import CashRegister, TransactionType as CashTransactionType
        from apps.school.finance.choices import ExpenseCategory
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # If creating cash transaction, validate cash register
        if create_cash_transaction:
            if not cash_register_id:
                raise ValueError("Cash register ID required for cash transaction")
            
            try:
                cash_register = CashRegister.objects.select_for_update().get(
                    id=cash_register_id,
                    branch=staff.branch
                )
            except CashRegister.DoesNotExist:
                raise ValueError("Cash register not found or doesn't belong to staff's branch")
        
        # Apply balance transaction
        balance_transaction = BalanceService.apply_transaction(
            membership=staff,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            reference=reference,
            processed_by=processed_by
        )
        
        result = {
            'success': True,
            'balance_transaction': balance_transaction,
            'previous_balance': balance_transaction.previous_balance,
            'new_balance': balance_transaction.new_balance,
            'cash_transaction': None
        }
        
        # Create cash transaction if requested and balance decreased (payment made)
        if create_cash_transaction and transaction_type in [TransactionType.DEDUCTION, TransactionType.FINE, TransactionType.ADVANCE, TransactionType.ADJUSTMENT]:
            # This is a payment from cash register to staff
            metadata = {}
            if processed_by:
                metadata['processed_by_id'] = str(processed_by.id)
                metadata['processed_by_name'] = processed_by.get_full_name()
            
            # Transaction yaratish - status='completed' bo'lgani uchun
            # Transaction.save() avtomatik ravishda kassa balansini yangilaydi
            cash_transaction = CashTransaction.objects.create(
                branch=staff.branch,
                cash_register=cash_register,
                transaction_type=CashTransactionType.SALARY,  # Using SALARY type for staff payments
                status='completed',
                expense_category=ExpenseCategory.SALARY,
                amount=amount,
                payment_method=payment_method,
                description=f"{description} - {staff.user.get_full_name()}",
                reference_number=reference or f"STAFF-{balance_transaction.id}",
                employee_membership=staff,
                metadata=metadata
            )
            
            # ESLATMA: Kassa balansi Transaction.save() metodida avtomatik yangilanadi
            # update_balance() ni qo'shimcha chaqirish shart emas
            
            result['cash_transaction'] = cash_transaction
        
        return result
    
    @staticmethod
    @transaction.atomic
    def process_salary_payment(
        staff,
        amount: int,
        payment_date,
        payment_method: str,
        month,
        payment_type: str = 'salary',
        notes: str = '',
        reference_number: str = '',
        processed_by = None
    ):
        """
        Process salary payment with all necessary records.
        
        Creates:
        1. SalaryPayment record
        2. BalanceTransaction record (deduction from balance)
        3. Updates staff balance
        
        Args:
            staff: BranchMembership instance
            amount: Payment amount
            payment_date: Payment date
            payment_method: Payment method (cash, bank_transfer, etc)
            month: Month for which salary is paid (DateField)
            payment_type: Payment type (advance, salary, bonus_payment, other)
            notes: Additional notes
            reference_number: Payment reference number
            processed_by: User who processed payment
            
        Returns:
            dict with payment details
        """
        from apps.branch.choices import PaymentStatus
        from django.utils import timezone
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Create salary payment record (no more unique constraint check)
        payment = SalaryPayment.objects.create(
            membership=staff,
            month=month,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            payment_type=payment_type,
            status=PaymentStatus.PAID,
            notes=notes,
            reference_number=reference_number,
            processed_by=processed_by
        )
        
        # Deduct from balance
        previous_balance = staff.balance
        staff.balance -= amount
        new_balance = staff.balance
        staff.save(update_fields=['balance', 'updated_at'])
        
        # Create balance transaction
        balance_transaction = BalanceTransaction.objects.create(
            membership=staff,
            transaction_type=TransactionType.DEDUCTION,
            amount=amount,
            previous_balance=previous_balance,
            new_balance=new_balance,
            description=f"Maosh to'lovi: {month.strftime('%Y-%m')}",
            reference=reference_number or f"SALARY-{payment.id}",
            salary_payment=payment,
            processed_by=processed_by
        )
        
        return {
            'success': True,
            'payment': payment,
            'balance_transaction': balance_transaction,
            'previous_balance': previous_balance,
            'new_balance': new_balance
        }
    
    @staticmethod
    def get_monthly_summary(staff, year: int, month: int):
        """
        Get salary summary for a specific month.
        
        Args:
            staff: BranchMembership instance
            year: Year
            month: Month (1-12)
            
        Returns:
            dict with summary
        """
        import calendar
        from datetime import date
        from django.db.models import Sum
        
        # Month date range
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get payments for this month
        payments = SalaryPayment.objects.filter(
            membership=staff,
            month__year=year,
            month__month=month
        )
        
        # Get salary transactions for this month
        transactions = BalanceTransaction.objects.filter(
            membership=staff,
            transaction_type=TransactionType.SALARY_ACCRUAL,
            created_at__date__gte=first_day,
            created_at__date__lte=last_day
        )
        
        total_accrued = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        total_paid = payments.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
        
        return {
            'year': year,
            'month': month,
            'total_accrued': total_accrued,
            'total_paid': total_paid,
            'balance_change': total_accrued - total_paid,
            'payments_count': payments.count(),
            'transactions_count': transactions.count()
        }
