"""HR app tests."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from apps.branch.models import Branch
from apps.hr.models import StaffRole, StaffProfile, BalanceTransaction, SalaryPayment
from apps.hr.services import BalanceService
from apps.hr.choices import (
    EmploymentType, StaffStatus, TransactionType,
    PaymentMethod, PaymentStatus
)

User = get_user_model()


class StaffRoleTests(TestCase):
    """Tests for StaffRole model."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Test Branch',
            slug='test-branch',
            type='school',
            status='active'
        )
    
    def test_create_staff_role(self):
        """Test creating a staff role."""
        role = StaffRole.objects.create(
            name='Oshpaz',
            code='cook',
            branch=self.branch,
            permissions=['view_menu', 'manage_inventory'],
            salary_range_min=3000000,
            salary_range_max=5000000,
        )
        
        self.assertEqual(role.name, 'Oshpaz')
        self.assertEqual(role.code, 'cook')
        self.assertEqual(role.branch, self.branch)
        self.assertTrue(role.is_active)
    
    def test_unique_code_per_branch(self):
        """Test that code must be unique per branch."""
        StaffRole.objects.create(
            name='Cook',
            code='cook',
            branch=self.branch,
            permissions=[]
        )
        
        # Same code in same branch should fail
        with self.assertRaises(Exception):
            StaffRole.objects.create(
                name='Chef',
                code='cook',
                branch=self.branch,
                permissions=[]
            )


class StaffProfileTests(TestCase):
    """Tests for StaffProfile model."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Test Branch',
            slug='test-branch',
            type='school',
            status='active'
        )
        
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='User'
        )
        
        self.role = StaffRole.objects.create(
            name='Teacher',
            code='teacher',
            branch=self.branch,
            permissions=['view_grades']
        )
    
    def test_create_staff_profile(self):
        """Test creating a staff profile."""
        profile = StaffProfile.objects.create(
            user=self.user,
            branch=self.branch,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000,
            status=StaffStatus.ACTIVE
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.branch, self.branch)
        self.assertEqual(profile.current_balance, 0)
        self.assertEqual(profile.status, StaffStatus.ACTIVE)
    
    def test_unique_user_branch(self):
        """Test that user-branch combination must be unique."""
        StaffProfile.objects.create(
            user=self.user,
            branch=self.branch,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
        
        # Same user in same branch should fail
        with self.assertRaises(Exception):
            StaffProfile.objects.create(
                user=self.user,
                branch=self.branch,
                staff_role=self.role,
                employment_type=EmploymentType.PART_TIME,
                hire_date=date.today(),
                base_salary=3000000
            )


class BalanceServiceTests(TestCase):
    """Tests for BalanceService."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Test Branch',
            slug='test-branch',
            type='school',
            status='active'
        )
        
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='User'
        )
        
        self.role = StaffRole.objects.create(
            name='Teacher',
            code='teacher',
            branch=self.branch,
            permissions=[]
        )
        
        self.staff = StaffProfile.objects.create(
            user=self.user,
            branch=self.branch,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000,
            current_balance=0
        )
    
    def test_deposit_increases_balance(self):
        """Test that deposit increases balance."""
        txn = BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.DEPOSIT,
            amount=1000000,
            description='Test deposit'
        )
        
        self.assertEqual(txn.amount, 1000000)
        self.assertEqual(txn.previous_balance, 0)
        self.assertEqual(txn.new_balance, 1000000)
        
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.current_balance, 1000000)
    
    def test_withdrawal_decreases_balance(self):
        """Test that withdrawal decreases balance."""
        # First deposit
        BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.DEPOSIT,
            amount=2000000,
            description='Initial deposit'
        )
        
        # Then withdraw
        txn = BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=500000,
            description='Test withdrawal'
        )
        
        self.assertEqual(txn.amount, 500000)
        self.assertEqual(txn.previous_balance, 2000000)
        self.assertEqual(txn.new_balance, 1500000)
        
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.current_balance, 1500000)
    
    def test_salary_payment_increases_balance(self):
        """Test that salary payment increases balance."""
        txn = BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.SALARY,
            amount=5000000,
            description='Monthly salary'
        )
        
        self.assertEqual(txn.new_balance, 5000000)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.current_balance, 5000000)
    
    def test_negative_amount_fails(self):
        """Test that negative amount raises error."""
        with self.assertRaises(ValueError):
            BalanceService.apply_transaction(
                staff=self.staff,
                transaction_type=TransactionType.DEPOSIT,
                amount=-1000000,
                description='Invalid'
            )
    
    def test_balance_summary(self):
        """Test balance summary calculation."""
        # Create transactions
        BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.SALARY,
            amount=5000000,
            description='Salary'
        )
        BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.BONUS,
            amount=500000,
            description='Bonus'
        )
        BalanceService.apply_transaction(
            staff=self.staff,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=1000000,
            description='Withdrawal'
        )
        
        # Refresh to get updated balance
        self.staff.refresh_from_db()
        
        summary = BalanceService.get_balance_summary(self.staff)
        
        self.assertEqual(summary['total_credits'], 5500000)
        self.assertEqual(summary['total_debits'], 1000000)
        self.assertEqual(summary['net'], 4500000)
        self.assertEqual(summary['current_balance'], 4500000)


class SalaryPaymentTests(TestCase):
    """Tests for SalaryPayment model and signal."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Test Branch',
            slug='test-branch',
            type='school',
            status='active'
        )
        
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='User'
        )
        
        self.role = StaffRole.objects.create(
            name='Teacher',
            code='teacher',
            branch=self.branch,
            permissions=[]
        )
        
        self.staff = StaffProfile.objects.create(
            user=self.user,
            branch=self.branch,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
    
    def test_create_salary_payment(self):
        """Test creating salary payment."""
        payment = SalaryPayment.objects.create(
            staff=self.staff,
            month=date(2024, 1, 1),
            amount=5000000,
            payment_date=date.today(),
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.PENDING
        )
        
        self.assertEqual(payment.staff, self.staff)
        self.assertEqual(payment.amount, 5000000)
        self.assertEqual(payment.status, PaymentStatus.PENDING)
    
    def test_paid_payment_creates_transaction(self):
        """Test that marking payment as paid creates balance transaction."""
        payment = SalaryPayment.objects.create(
            staff=self.staff,
            month=date(2024, 1, 1),
            amount=5000000,
            payment_date=date.today(),
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.PAID
        )
        
        # Signal should create transaction
        self.assertTrue(payment.transactions.exists())
        
        txn = payment.transactions.first()
        self.assertEqual(txn.transaction_type, TransactionType.SALARY)
        self.assertEqual(txn.amount, 5000000)
        
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.current_balance, 5000000)
    
    def test_unique_staff_month(self):
        """Test that staff-month combination must be unique."""
        SalaryPayment.objects.create(
            staff=self.staff,
            month=date(2024, 1, 1),
            amount=5000000,
            payment_date=date.today(),
            payment_method=PaymentMethod.CASH,
            status=PaymentStatus.PENDING
        )
        
        # Same staff and month should fail
        with self.assertRaises(Exception):
            SalaryPayment.objects.create(
                staff=self.staff,
                month=date(2024, 1, 1),
                amount=4000000,
                payment_date=date.today(),
                payment_method=PaymentMethod.BANK_TRANSFER,
                status=PaymentStatus.PENDING
            )
