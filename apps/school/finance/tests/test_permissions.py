"""
Moliya tizimi permissions testlari.
CAN_AUTO_APPROVE va CAN_APPROVE_MANUALLY ruxsatlarini tekshirish.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, Role, BranchRole
from apps.school.finance.models import (
    CashRegister,
    FinanceCategory,
    Transaction,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
)
from apps.school.finance.permissions import FinancePermissions

User = get_user_model()


class AutoApprovePermissionTest(TestCase):
    """CAN_AUTO_APPROVE permission testlari."""

    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        # Branch yaratish
        self.branch = Branch.objects.create(
            name="Test Branch",
            type="school",
            slug="test-branch",
            address="Test Address"
        )

        # Kassa yaratish
        self.cash_register = CashRegister.objects.create(
            branch=self.branch,
            name="Test Kassa",
            balance=5000000
        )

        # Kategoriyalar yaratish
        self.income_category = FinanceCategory.objects.create(
            branch=self.branch,
            name="Test Income",
            type="income"
        )

        self.expense_category = FinanceCategory.objects.create(
            branch=self.branch,
            name="Test Expense",
            type="expense"
        )

        # Branch Admin - har doim auto approve
        self.branch_admin_user = User.objects.create_user(
            phone_number="+998901234501",
            password="testpass123"
        )
        self.branch_admin_membership = BranchMembership.objects.create(
            user=self.branch_admin_user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
        )

        # Accountant with CAN_AUTO_APPROVE permission
        self.accountant_auto_user = User.objects.create_user(
            phone_number="+998901234502",
            password="testpass123"
        )
        self.accountant_auto_role = Role.objects.create(
            branch=self.branch,
            name="Accountant Auto",
            permissions={
                FinancePermissions.CREATE_TRANSACTIONS: True,
                FinancePermissions.CAN_AUTO_APPROVE: True,
            }
        )
        self.accountant_auto_membership = BranchMembership.objects.create(
            user=self.accountant_auto_user,
            branch=self.branch,
            role=BranchRole.OTHER,
            role_ref=self.accountant_auto_role
        )

        # Accountant WITHOUT CAN_AUTO_APPROVE (manual approval)
        self.accountant_manual_user = User.objects.create_user(
            phone_number="+998901234503",
            password="testpass123"
        )
        self.accountant_manual_role = Role.objects.create(
            branch=self.branch,
            name="Accountant Manual",
            permissions={
                FinancePermissions.CREATE_TRANSACTIONS: True,
                FinancePermissions.CAN_APPROVE_MANUALLY: True,
                # NO CAN_AUTO_APPROVE
            }
        )
        self.accountant_manual_membership = BranchMembership.objects.create(
            user=self.accountant_manual_user,
            branch=self.branch,
            role=BranchRole.OTHER,
            role_ref=self.accountant_manual_role
        )

        # Super Admin with CAN_AUTO_APPROVE
        self.super_admin_auto_user = User.objects.create_user(
            phone_number="+998901234504",
            password="testpass123"
        )
        self.super_admin_auto_role = Role.objects.create(
            branch=self.branch,
            name="Super Admin Auto",
            permissions={
                FinancePermissions.CAN_AUTO_APPROVE: True,
            }
        )
        self.super_admin_auto_membership = BranchMembership.objects.create(
            user=self.super_admin_auto_user,
            branch=self.branch,
            role=BranchRole.SUPER_ADMIN,
            role_ref=self.super_admin_auto_role
        )

        # Super Admin WITHOUT CAN_AUTO_APPROVE (manual approval)
        self.super_admin_manual_user = User.objects.create_user(
            phone_number="+998901234505",
            password="testpass123"
        )
        self.super_admin_manual_role = Role.objects.create(
            branch=self.branch,
            name="Super Admin Manual",
            permissions={
                FinancePermissions.CAN_APPROVE_MANUALLY: True,
                # NO CAN_AUTO_APPROVE
            }
        )
        self.super_admin_manual_membership = BranchMembership.objects.create(
            user=self.super_admin_manual_user,
            branch=self.branch,
            role=BranchRole.SUPER_ADMIN,
            role_ref=self.super_admin_manual_role
        )

        self.client = APIClient()

    def test_branch_admin_auto_approves_income(self):
        """Branch Admin kirim yaratganda avtomatik COMPLETED bo'lishi kerak."""
        self.client.force_authenticate(user=self.branch_admin_user)

        initial_balance = self.cash_register.balance

        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 1000000,
            "payment_method": PaymentMethod.CASH,
            "description": "Test income"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.COMPLETED)

        # Kassa balansi avtomatik yangilangan
        self.cash_register.refresh_from_db()
        self.assertEqual(
            self.cash_register.balance,
            initial_balance + 1000000
        )

    def test_branch_admin_auto_approves_expense(self):
        """Branch Admin chiqim yaratganda avtomatik COMPLETED bo'lishi kerak."""
        self.client.force_authenticate(user=self.branch_admin_user)

        initial_balance = self.cash_register.balance

        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.EXPENSE,
            "category": str(self.expense_category.id),
            "amount": 500000,
            "payment_method": PaymentMethod.CASH,
            "description": "Test expense"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.COMPLETED)

        # Kassa balansi avtomatik ayrilgan
        self.cash_register.refresh_from_db()
        self.assertEqual(
            self.cash_register.balance,
            initial_balance - 500000
        )

    def test_accountant_with_auto_approve_creates_completed(self):
        """CAN_AUTO_APPROVE ruxsati bor accountant COMPLETED yaratishi kerak."""
        self.client.force_authenticate(user=self.accountant_auto_user)

        initial_balance = self.cash_register.balance

        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 2000000,
            "payment_method": PaymentMethod.CASH,
            "description": "Accountant auto income"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.COMPLETED)

        # Kassa balansi avtomatik yangilangan
        self.cash_register.refresh_from_db()
        self.assertEqual(
            self.cash_register.balance,
            initial_balance + 2000000
        )

    def test_accountant_without_auto_approve_creates_pending(self):
        """CAN_AUTO_APPROVE yo'q accountant PENDING yaratishi kerak."""
        self.client.force_authenticate(user=self.accountant_manual_user)

        initial_balance = self.cash_register.balance

        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 1500000,
            "payment_method": PaymentMethod.CASH,
            "description": "Accountant manual income"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.PENDING)

        # Kassa balansi YANGILANMAGAN (pending)
        self.cash_register.refresh_from_db()
        self.assertEqual(self.cash_register.balance, initial_balance)

    def test_super_admin_with_auto_approve_creates_completed(self):
        """CAN_AUTO_APPROVE ruxsati bor super admin COMPLETED yaratishi kerak."""
        self.client.force_authenticate(user=self.super_admin_auto_user)

        initial_balance = self.cash_register.balance

        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.EXPENSE,
            "category": str(self.expense_category.id),
            "amount": 300000,
            "payment_method": PaymentMethod.CASH,
            "description": "Super admin auto expense"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.COMPLETED)

        # Kassa balansi avtomatik ayrilgan
        self.cash_register.refresh_from_db()
        self.assertEqual(
            self.cash_register.balance,
            initial_balance - 300000
        )

    def test_super_admin_without_auto_approve_creates_pending(self):
        """CAN_AUTO_APPROVE yo'q super admin PENDING yaratishi kerak."""
        self.client.force_authenticate(user=self.super_admin_manual_user)

        initial_balance = self.cash_register.balance

        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.EXPENSE,
            "category": str(self.expense_category.id),
            "amount": 800000,
            "payment_method": PaymentMethod.CASH,
            "description": "Super admin manual expense"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.PENDING)

        # Kassa balansi YANGILANMAGAN (pending)
        self.cash_register.refresh_from_db()
        self.assertEqual(self.cash_register.balance, initial_balance)

    def test_pending_transaction_does_not_affect_balance(self):
        """PENDING transaction kassa balansini o'zgartirmasligi kerak."""
        self.client.force_authenticate(user=self.accountant_manual_user)

        initial_balance = self.cash_register.balance

        # Income transaction
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 5000000,
            "payment_method": PaymentMethod.CASH,
            "description": "Large pending income"
        }

        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.PENDING)

        # Kassa balansi o'zgarmagan
        self.cash_register.refresh_from_db()
        self.assertEqual(self.cash_register.balance, initial_balance)

        # Transaction bazada PENDING holatda
        transaction = Transaction.objects.get(id=response.data['id'])
        self.assertEqual(transaction.status, TransactionStatus.PENDING)
