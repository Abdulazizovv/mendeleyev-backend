"""
Finance domain services.

Bu faylda view/serializerlardan ajratilgan biznes logikalar turadi.
"""
from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from .models import (
    StudentBalance,
    StudentBalanceTransaction,
    StudentBalanceTransactionReason,
    StudentBalanceTransactionStatus,
    StudentBalanceTransactionType,
    StudentSubscription,
)


@dataclass(frozen=True)
class SubscriptionChargeResult:
    ok: bool
    charged: bool
    amount: int
    reason: str
    message: str
    student_balance_id: str
    subscription_id: str
    new_balance: int | None = None
    debt_added: int = 0


def charge_subscription_from_student_balance(
    *,
    subscription: StudentSubscription,
    processed_by=None,
    force: bool = False,
    occurred_at=None,
) -> SubscriptionChargeResult:
    """
    Abonement uchun student balansdan pul yechish.

    Qoidalar:
    - next_payment_date <= bugun bo'lsa (yoki force=True) charge qilinadi
    - Yetarli balans bo'lmasa: balansdan yechmaymiz, subscription.total_debt ga yozamiz
      va next_payment_date ni keyingi davrga suramiz.
    - Audit: har urinish StudentBalanceTransaction sifatida yoziladi.
    """
    occurred_at = occurred_at or timezone.now()
    today = occurred_at.date()

    with transaction.atomic():
        locked_subscription = (
            StudentSubscription.objects.select_related("subscription_plan", "branch", "discount", "student_profile")
            # discount nullable FK bo'lgani uchun Postgresda outer join + FOR UPDATE muammosi chiqmasligi uchun
            # faqat subscription jadvalini lock qilamiz.
            .select_for_update(of=("self",))
            .get(id=subscription.id)
        )

        if locked_subscription.deleted_at is not None or not locked_subscription.is_active:
            return SubscriptionChargeResult(
                ok=True,
                charged=False,
                amount=0,
                reason="inactive",
                message="Subscription inactive/deleted",
                student_balance_id="",
                subscription_id=str(locked_subscription.id),
            )

        if locked_subscription.end_date and today > locked_subscription.end_date:
            return SubscriptionChargeResult(
                ok=True,
                charged=False,
                amount=0,
                reason="expired",
                message="Subscription expired",
                student_balance_id="",
                subscription_id=str(locked_subscription.id),
            )

        if not force and locked_subscription.next_payment_date > today:
            return SubscriptionChargeResult(
                ok=True,
                charged=False,
                amount=0,
                reason="not_due",
                message="Next payment date not reached",
                student_balance_id="",
                subscription_id=str(locked_subscription.id),
            )

        base_amount = int(locked_subscription.subscription_plan.price)
        discount_amount = 0
        if locked_subscription.discount and locked_subscription.discount.is_valid():
            discount_amount = int(
                locked_subscription.discount.calculate_discount(base_amount, transaction_branch=locked_subscription.branch)
            )
        due_amount = base_amount - discount_amount
        if due_amount <= 0:
            due_amount = 0

        student_balance, _ = StudentBalance.objects.select_for_update().get_or_create(
            student_profile=locked_subscription.student_profile,
            defaults={"balance": 0},
        )

        if due_amount == 0:
            return SubscriptionChargeResult(
                ok=True,
                charged=False,
                amount=0,
                reason="zero",
                message="Due amount is 0",
                student_balance_id=str(student_balance.id),
                subscription_id=str(locked_subscription.id),
                new_balance=student_balance.balance,
            )

        if student_balance.balance >= due_amount:
            next_payment_date_before = locked_subscription.next_payment_date
            student_balance.subtract_amount(
                due_amount,
                reason=StudentBalanceTransactionReason.SUBSCRIPTION_CHARGE,
                processed_by=processed_by,
                subscription=locked_subscription,
                reference=str(locked_subscription.id),
                description="Abonement uchun balansdan avtomatik yechildi",
                metadata={
                    "base_amount": base_amount,
                    "discount_amount": discount_amount,
                    "next_payment_date_before": next_payment_date_before.isoformat() if next_payment_date_before else None,
                },
                occurred_at=occurred_at,
            )

            locked_subscription.update_next_payment_date()
            locked_subscription.last_payment_date = today
            locked_subscription.save(update_fields=["last_payment_date", "updated_at"])

            return SubscriptionChargeResult(
                ok=True,
                charged=True,
                amount=due_amount,
                reason="debited",
                message="Charged from balance",
                student_balance_id=str(student_balance.id),
                subscription_id=str(locked_subscription.id),
                new_balance=student_balance.balance,
            )

        # Yetarli balans yo'q: qarzga yozamiz va audit yozamiz (FAILED debit)
        previous_balance = int(student_balance.balance)
        next_payment_date_before = locked_subscription.next_payment_date
        locked_subscription.add_debt(due_amount)
        locked_subscription.update_next_payment_date()

        StudentBalanceTransaction.objects.create(
            student_balance=student_balance,
            subscription=locked_subscription,
            transaction_type=StudentBalanceTransactionType.DEBIT,
            status=StudentBalanceTransactionStatus.FAILED,
            reason=StudentBalanceTransactionReason.SUBSCRIPTION_CHARGE,
            amount=due_amount,
            previous_balance=previous_balance,
            new_balance=previous_balance,
            reference=str(locked_subscription.id),
            description="Balans yetarli emas, summa qarzga yozildi",
            metadata={
                "base_amount": base_amount,
                "discount_amount": discount_amount,
                "debt_added": due_amount,
                "balance_available": previous_balance,
                "next_payment_date_before": next_payment_date_before.isoformat() if next_payment_date_before else None,
            },
            processed_by=processed_by,
            occurred_at=occurred_at,
            created_by=processed_by,
            updated_by=processed_by,
        )

        return SubscriptionChargeResult(
            ok=True,
            charged=False,
            amount=due_amount,
            reason="debt_added",
            message="Insufficient balance, added to debt",
            student_balance_id=str(student_balance.id),
            subscription_id=str(locked_subscription.id),
            new_balance=student_balance.balance,
            debt_added=due_amount,
        )
