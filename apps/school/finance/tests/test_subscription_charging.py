from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile, StudentStatus
from apps.school.finance.models import (
    StudentBalance,
    StudentBalanceTransaction,
    StudentBalanceTransactionReason,
    StudentBalanceTransactionStatus,
    SubscriptionPlan,
    SubscriptionPeriod,
    StudentSubscription,
)
from apps.school.finance.services import charge_subscription_from_student_balance

User = get_user_model()


class SubscriptionChargingServiceTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active",
        )

        self.student_user = User.objects.create_user(
            phone_number="+998900000001",
            password="testpass123",
            first_name="Ali",
            last_name="Valiyev",
        )
        self.student_membership = BranchMembership.objects.create(
            user=self.student_user,
            branch=self.branch,
            role=BranchRole.STUDENT,
        )
        # StudentProfile BranchMembership signal orqali avtomatik yaratiladi
        self.student_profile = StudentProfile.objects.get(user_branch=self.student_membership)
        self.student_profile.status = StudentStatus.ACTIVE
        self.student_profile.save(update_fields=["status", "updated_at"])

        self.plan = SubscriptionPlan.objects.create(
            branch=self.branch,
            grade_level_min=1,
            grade_level_max=11,
            period=SubscriptionPeriod.MONTHLY,
            price=1_000_000,
            is_active=True,
            name="Test plan",
        )

        today = date.today()
        self.subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            is_active=True,
            start_date=today,
            next_payment_date=today,
            total_debt=0,
        )

    def test_charge_success_debits_balance_and_updates_subscription(self):
        student_balance = StudentBalance.objects.get(student_profile=self.student_profile)
        student_balance.add_amount(
            2_000_000,
            reason=StudentBalanceTransactionReason.MANUAL_ADJUSTMENT,
            description="Initial topup for test",
        )

        result = charge_subscription_from_student_balance(subscription=self.subscription, processed_by=None, force=False)
        self.assertTrue(result.ok)
        self.assertTrue(result.charged)
        self.assertEqual(result.amount, 1_000_000)

        student_balance.refresh_from_db()
        self.assertEqual(student_balance.balance, 1_000_000)

        self.subscription.refresh_from_db()
        self.assertIsNotNone(self.subscription.last_payment_date)
        self.assertGreater(self.subscription.next_payment_date, date.today())

        self.assertTrue(
            StudentBalanceTransaction.objects.filter(
                student_balance=student_balance,
                subscription=self.subscription,
                reason=StudentBalanceTransactionReason.SUBSCRIPTION_CHARGE,
                status=StudentBalanceTransactionStatus.COMPLETED,
                amount=1_000_000,
            ).exists()
        )

    def test_charge_insufficient_adds_debt_and_writes_failed_audit(self):
        student_balance = StudentBalance.objects.get(student_profile=self.student_profile)
        initial_next_due = self.subscription.next_payment_date

        result = charge_subscription_from_student_balance(subscription=self.subscription, processed_by=None, force=False)
        self.assertTrue(result.ok)
        self.assertFalse(result.charged)
        self.assertEqual(result.debt_added, 1_000_000)

        student_balance.refresh_from_db()
        self.assertEqual(student_balance.balance, 0)

        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.total_debt, 1_000_000)
        self.assertGreater(self.subscription.next_payment_date, initial_next_due)

        self.assertTrue(
            StudentBalanceTransaction.objects.filter(
                student_balance=student_balance,
                subscription=self.subscription,
                reason=StudentBalanceTransactionReason.SUBSCRIPTION_CHARGE,
                status=StudentBalanceTransactionStatus.FAILED,
                amount=1_000_000,
            ).exists()
        )


class SubscriptionChargingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active",
        )

        self.admin_user = User.objects.create_user(
            phone_number="+998900000010",
            password="testpass123",
        )
        BranchMembership.objects.create(
            user=self.admin_user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN,
        )
        self.client.force_authenticate(user=self.admin_user)

        self.student_user = User.objects.create_user(
            phone_number="+998900000011",
            password="testpass123",
        )
        self.student_membership = BranchMembership.objects.create(
            user=self.student_user,
            branch=self.branch,
            role=BranchRole.STUDENT,
        )
        self.student_profile = StudentProfile.objects.get(user_branch=self.student_membership)
        self.student_profile.status = StudentStatus.ACTIVE
        self.student_profile.save(update_fields=["status", "updated_at"])

        self.plan = SubscriptionPlan.objects.create(
            branch=self.branch,
            grade_level_min=1,
            grade_level_max=11,
            period=SubscriptionPeriod.MONTHLY,
            price=500_000,
            is_active=True,
            name="Test plan",
        )

        today = date.today()
        self.subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            is_active=True,
            start_date=today,
            next_payment_date=today,
            total_debt=0,
        )

    def test_manual_charge_endpoint(self):
        student_balance = StudentBalance.objects.get(student_profile=self.student_profile)
        student_balance.add_amount(
            500_000,
            reason=StudentBalanceTransactionReason.MANUAL_ADJUSTMENT,
            description="Topup before manual charge",
        )

        url = f"/api/v1/school/finance/student-subscriptions/{self.subscription.id}/charge/"
        response = self.client.post(url, {"force": False}, format="json", HTTP_X_BRANCH_ID=str(self.branch.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["result"]["ok"])
        self.assertTrue(response.data["result"]["charged"])

        student_balance.refresh_from_db()
        self.assertEqual(student_balance.balance, 0)
