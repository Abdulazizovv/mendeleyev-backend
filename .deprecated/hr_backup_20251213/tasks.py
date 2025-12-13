"""HR Celery tasks for async operations."""

from celery import shared_task
from django.db import transaction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_bulk_salary_payments(self, month: str, payments: list, processed_by_id: str):
    """
    Process bulk salary payments asynchronously.
    
    Args:
        month: Payment month in YYYY-MM-DD format
        payments: List of payment dicts with staff_id, amount, payment_date, etc.
        processed_by_id: User ID who initiated the bulk payment
    
    Returns:
        Dict with results (success count, failed count, errors)
    """
    from apps.hr.models import StaffProfile, SalaryPayment
    from apps.hr.choices import PaymentStatus
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        month_date = datetime.strptime(month, '%Y-%m-%d').date()
        processed_by = User.objects.get(pk=processed_by_id)
    except (ValueError, User.DoesNotExist) as e:
        logger.error(f"Invalid month or user: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    
    results = {
        'success_count': 0,
        'failed_count': 0,
        'errors': []
    }
    
    for payment_data in payments:
        try:
            with transaction.atomic():
                staff = StaffProfile.objects.select_for_update().get(
                    pk=payment_data['staff_id'],
                    deleted_at__isnull=True
                )
                
                # Check if payment already exists for this month
                existing = SalaryPayment.objects.filter(
                    staff=staff,
                    month=month_date,
                    deleted_at__isnull=True
                ).exists()
                
                if existing:
                    logger.warning(f"Payment already exists for staff {staff.id} for month {month}")
                    results['failed_count'] += 1
                    results['errors'].append({
                        'staff_id': staff.id,
                        'error': 'Bu oy uchun maosh allaqachon to\'langan'
                    })
                    continue
                
                # Create payment
                payment = SalaryPayment.objects.create(
                    staff=staff,
                    month=month_date,
                    amount=payment_data['amount'],
                    payment_date=datetime.strptime(payment_data['payment_date'], '%Y-%m-%d').date(),
                    payment_method=payment_data['payment_method'],
                    status=PaymentStatus.PAID,  # Mark as paid immediately
                    notes=payment_data.get('notes', ''),
                    reference_number=f"BULK-{month_date.strftime('%Y%m')}-{staff.id}",
                    processed_by=processed_by
                )
                
                results['success_count'] += 1
                logger.info(f"Created salary payment {payment.id} for staff {staff.id}")
                
        except StaffProfile.DoesNotExist:
            logger.error(f"Staff {payment_data['staff_id']} not found")
            results['failed_count'] += 1
            results['errors'].append({
                'staff_id': payment_data['staff_id'],
                'error': 'Xodim topilmadi'
            })
        except Exception as e:
            logger.error(f"Error processing payment for staff {payment_data['staff_id']}: {e}")
            results['failed_count'] += 1
            results['errors'].append({
                'staff_id': payment_data.get('staff_id'),
                'error': str(e)
            })
    
    logger.info(f"Bulk salary payments processed: {results}")
    return results


@shared_task
def reconcile_staff_balances():
    """
    Reconcile staff balances with transaction history.
    
    This task runs periodically to ensure data integrity.
    Finds discrepancies between current_balance and sum of transactions.
    """
    from apps.hr.models import StaffProfile, BalanceTransaction
    from django.db.models import Sum, Q
    from apps.hr.choices import TransactionType
    
    discrepancies = []
    
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
    
    for staff in StaffProfile.objects.filter(deleted_at__isnull=True):
        transactions = BalanceTransaction.objects.filter(
            staff=staff,
            deleted_at__isnull=True
        )
        
        total_credits = transactions.filter(
            transaction_type__in=credit_types
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_debits = transactions.filter(
            transaction_type__in=debit_types
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        calculated_balance = total_credits - total_debits
        
        if calculated_balance != staff.current_balance:
            discrepancy = {
                'staff_id': staff.id,
                'staff_name': staff.user.get_full_name() or staff.user.phone_number,
                'current_balance': staff.current_balance,
                'calculated_balance': calculated_balance,
                'difference': calculated_balance - staff.current_balance
            }
            discrepancies.append(discrepancy)
            logger.warning(f"Balance discrepancy found: {discrepancy}")
    
    if discrepancies:
        logger.error(f"Found {len(discrepancies)} balance discrepancies")
        # You could send an email or notification here
    else:
        logger.info("All staff balances are consistent")
    
    return {
        'total_checked': StaffProfile.objects.filter(deleted_at__isnull=True).count(),
        'discrepancies_found': len(discrepancies),
        'discrepancies': discrepancies
    }


@shared_task
def generate_monthly_salary_report(month: str, branch_id: int = None):
    """
    Generate monthly salary report and optionally email it.
    
    Args:
        month: Month in YYYY-MM-DD format
        branch_id: Optional branch ID to filter by
    
    Returns:
        Dict with report data
    """
    from apps.hr.models import SalaryPayment, StaffProfile
    from django.db.models import Sum, Count, Q
    from datetime import datetime
    
    try:
        month_date = datetime.strptime(month, '%Y-%m-%d').date()
    except ValueError as e:
        logger.error(f"Invalid month format: {e}")
        return {'success': False, 'error': str(e)}
    
    qs = SalaryPayment.objects.filter(
        month=month_date,
        deleted_at__isnull=True
    )
    
    if branch_id:
        qs = qs.filter(staff__branch_id=branch_id)
    
    # Aggregate stats
    total_stats = qs.aggregate(
        total_staff=Count('staff', distinct=True),
        total_paid=Count('id', filter=Q(status='paid')),
        total_pending=Count('id', filter=Q(status='pending')),
        total_amount_paid=Sum('amount', filter=Q(status='paid')) or 0,
        total_amount_pending=Sum('amount', filter=Q(status='pending')) or 0,
    )
    
    # By role
    by_role = list(qs.values(
        'staff__staff_role__name',
        'staff__staff_role__id'
    ).annotate(
        count=Count('id'),
        paid_count=Count('id', filter=Q(status='paid')),
        total_paid=Sum('amount', filter=Q(status='paid')) or 0,
        total_pending=Sum('amount', filter=Q(status='pending')) or 0,
    ).order_by('-total_paid'))
    
    # By payment method
    by_method = list(qs.filter(status='paid').values(
        'payment_method'
    ).annotate(
        count=Count('id'),
        total=Sum('amount') or 0
    ))
    
    report = {
        'month': month_date.strftime('%Y-%m'),
        'branch_id': branch_id,
        'generated_at': datetime.now().isoformat(),
        'summary': total_stats,
        'by_role': by_role,
        'by_payment_method': by_method
    }
    
    logger.info(f"Generated salary report for {month_date.strftime('%Y-%m')}")
    return report
