"""HR app tests."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

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


class StaffCreateAPITests(APITestCase):
    """Tests for enhanced StaffCreateView."""
    
    def setUp(self):
        self.client = APIClient()
        self.branch = Branch.objects.create(
            name='Test Branch',
            slug='test-branch',
            type='school',
            status='active'
        )
        
        self.admin_user = User.objects.create_user(
            phone_number='+998901111111',
            first_name='Admin',
            last_name='User'
        )
        
        self.role = StaffRole.objects.create(
            name='Teacher',
            code='teacher',
            branch=self.branch,
            permissions=['view_grades'],
            salary_range_min=3000000,
            salary_range_max=8000000
        )
        
        self.client.force_authenticate(user=self.admin_user)
        self.url = reverse('hr:staff-create')
    
    def test_create_staff_with_new_user(self):
        """Test creating staff with new user."""
        data = {
            'phone_number': '+998901234567',
            'first_name': 'Test',
            'last_name': 'Staff',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'branch_id': str(self.branch.id),
            'staff_role_id': str(self.role.id),
            'employment_type': 'full_time',
            'hire_date': date.today().isoformat(),
            'base_salary': 5000000,
            'bank_account': '1234567890',
            'tax_id': '123456789'
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check user created
        user = User.objects.get(phone_number='+998901234567')
        self.assertEqual(user.first_name, 'Test')
        self.assertTrue(user.check_password('TestPass123!'))
        
        # Check staff profile created
        staff = StaffProfile.objects.get(user=user)
        self.assertEqual(staff.branch, self.branch)
        self.assertEqual(staff.staff_role, self.role)
        self.assertEqual(staff.base_salary, 5000000)
    
    def test_create_staff_phone_normalization(self):
        """Test phone number normalization."""
        data = {
            'phone_number': '90 123 45 67',  # Will be normalized to +998901234567
            'first_name': 'Test',
            'branch_id': str(self.branch.id),
            'staff_role_id': str(self.role.id),
            'employment_type': 'full_time',
            'hire_date': date.today().isoformat(),
            'base_salary': 5000000
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(first_name='Test')
        self.assertEqual(user.phone_number, '+998901234567')
    
    def test_create_staff_salary_validation(self):
        """Test salary range validation."""
        data = {
            'phone_number': '+998901234567',
            'first_name': 'Test',
            'branch_id': str(self.branch.id),
            'staff_role_id': str(self.role.id),
            'employment_type': 'full_time',
            'hire_date': date.today().isoformat(),
            'base_salary': 2000000  # Below min (3000000)
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('base_salary', response.data)
    
    def test_create_staff_duplicate_prevention(self):
        """Test duplicate staff prevention."""
        user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Existing'
        )
        
        StaffProfile.objects.create(
            user=user,
            branch=self.branch,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
        
        data = {
            'phone_number': '+998901234567',
            'first_name': 'Test',
            'branch_id': str(self.branch.id),
            'staff_role_id': str(self.role.id),
            'employment_type': 'full_time',
            'hire_date': date.today().isoformat(),
            'base_salary': 5000000
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
    
    def test_create_staff_role_branch_mismatch(self):
        """Test role-branch mismatch validation."""
        other_branch = Branch.objects.create(
            name='Other Branch',
            slug='other-branch',
            type='school',
            status='active'
        )
        
        other_role = StaffRole.objects.create(
            name='Cook',
            code='cook',
            branch=other_branch,
            permissions=[]
        )
        
        data = {
            'phone_number': '+998901234567',
            'first_name': 'Test',
            'branch_id': str(self.branch.id),
            'staff_role_id': str(other_role.id),  # Different branch
            'employment_type': 'full_time',
            'hire_date': date.today().isoformat(),
            'base_salary': 5000000
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('staff_role_id', response.data)


class StaffCheckViewTests(APITestCase):
    """Tests for StaffCheckView."""
    
    def setUp(self):
        self.client = APIClient()
        self.branch1 = Branch.objects.create(
            name='Toshkent filiali',
            slug='toshkent',
            type='school',
            status='active'
        )
        self.branch2 = Branch.objects.create(
            name='Samarqand filiali',
            slug='samarqand',
            type='school',
            status='active'
        )
        
        self.admin_user = User.objects.create_user(
            phone_number='+998901111111',
            first_name='Admin',
            last_name='User'
        )
        
        self.role1 = StaffRole.objects.create(
            name='Teacher',
            code='teacher',
            branch=self.branch1,
            permissions=['view_grades']
        )
        
        self.role2 = StaffRole.objects.create(
            name='Cook',
            code='cook',
            branch=self.branch2,
            permissions=['view_menu']
        )
        
        self.client.force_authenticate(user=self.admin_user)
        self.url = reverse('hr:staff-check-user')
    
    def test_user_not_exists(self):
        """Test when user doesn't exist."""
        response = self.client.get(self.url, {'phone_number': '+998909999999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['exists_in_branch'])
        self.assertFalse(response.data['exists_globally'])
        self.assertIsNone(response.data['branch_data'])
        self.assertEqual(len(response.data['all_branches_data']), 0)
    
    def test_user_exists_in_branch(self):
        """Test when user exists in specified branch."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='Staff'
        )
        
        from apps.branch.models import BranchMembership
        membership = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch1,
            role='staff'
        )
        
        staff_profile = StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch1,
            membership=membership,
            staff_role=self.role1,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
        
        response = self.client.get(self.url, {
            'phone_number': '+998901234567',
            'branch_id': str(self.branch1.id)
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists_in_branch'])
        self.assertTrue(response.data['exists_globally'])
        self.assertIsNotNone(response.data['branch_data'])
        
        branch_data = response.data['branch_data']
        self.assertEqual(branch_data['branch_name'], 'Toshkent filiali')
        self.assertEqual(branch_data['user']['phone_number'], '+998901234567')
        self.assertEqual(branch_data['staff_profile']['staff_role']['name'], 'Teacher')
    
    def test_user_exists_in_multiple_branches(self):
        """Test when user exists in multiple branches."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='Staff'
        )
        
        from apps.branch.models import BranchMembership
        
        # Branch 1
        membership1 = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch1,
            role='staff'
        )
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch1,
            membership=membership1,
            staff_role=self.role1,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
        
        # Branch 2
        membership2 = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch2,
            role='staff'
        )
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch2,
            membership=membership2,
            staff_role=self.role2,
            employment_type=EmploymentType.PART_TIME,
            hire_date=date.today(),
            base_salary=3000000
        )
        
        response = self.client.get(self.url, {'phone_number': '+998901234567'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists_globally'])
        self.assertEqual(len(response.data['all_branches_data']), 2)
        
        # Check both branches present
        branch_names = [d['branch_name'] for d in response.data['all_branches_data']]
        self.assertIn('Toshkent filiali', branch_names)
        self.assertIn('Samarqand filiali', branch_names)
    
    def test_phone_normalization(self):
        """Test phone number normalization."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='Staff'
        )
        
        from apps.branch.models import BranchMembership
        membership = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch1,
            role='staff'
        )
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch1,
            membership=membership,
            staff_role=self.role1,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
        
        # Test without +
        response = self.client.get(self.url, {'phone_number': '998901234567'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists_globally'])
    
    def test_post_method(self):
        """Test POST method works same as GET."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='Staff'
        )
        
        from apps.branch.models import BranchMembership
        membership = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch1,
            role='staff'
        )
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch1,
            membership=membership,
            staff_role=self.role1,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000
        )
        
        response = self.client.post(self.url, {
            'phone_number': '+998901234567',
            'branch_id': str(self.branch1.id)
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists_in_branch'])


class StaffListAPITests(APITestCase):
    """Tests for enhanced StaffProfileViewSet list."""
    
    def setUp(self):
        self.client = APIClient()
        self.branch = Branch.objects.create(
            name='Test Branch',
            slug='test-branch',
            type='school',
            status='active'
        )
        
        self.admin_user = User.objects.create_user(
            phone_number='+998901111111',
            first_name='Admin',
            last_name='User'
        )
        
        self.role = StaffRole.objects.create(
            name='Teacher',
            code='teacher',
            branch=self.branch,
            permissions=['view_grades']
        )
        
        self.client.force_authenticate(user=self.admin_user)
        self.url = reverse('hr:staffprofile-list')
    
    def test_list_staff_enhanced_fields(self):
        """Test list returns enhanced fields."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test',
            last_name='Staff',
            email='test@example.com'
        )
        
        from apps.branch.models import BranchMembership
        membership = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch,
            role='staff'
        )
        
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch,
            membership=membership,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000,
            current_balance=2500000
        )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data['results'][0]
        
        # Check enhanced fields
        self.assertIn('user_name', data)
        self.assertIn('phone_number', data)
        self.assertIn('email', data)
        self.assertIn('employment_type_display', data)
        self.assertIn('status_display', data)
        self.assertIn('balance_status', data)
        self.assertIn('days_employed', data)
        self.assertIn('is_active_membership', data)
        
        # Verify values
        self.assertEqual(data['phone_number'], '+998901234567')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['balance_status'], 'positive')
        self.assertIsNotNone(data['days_employed'])
    
    def test_filter_by_balance_status(self):
        """Test filtering by balance status."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test'
        )
        
        from apps.branch.models import BranchMembership
        membership = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch,
            role='staff'
        )
        
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch,
            membership=membership,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000,
            current_balance=2500000  # positive
        )
        
        response = self.client.get(self.url, {'balance_status': 'positive'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        response = self.client.get(self.url, {'balance_status': 'negative'})
        self.assertEqual(response.data['count'], 0)
    
    def test_staff_stats(self):
        """Test staff statistics endpoint."""
        staff_user = User.objects.create_user(
            phone_number='+998901234567',
            first_name='Test'
        )
        
        from apps.branch.models import BranchMembership
        membership = BranchMembership.objects.create(
            user=staff_user,
            branch=self.branch,
            role='staff'
        )
        
        StaffProfile.objects.create(
            user=staff_user,
            branch=self.branch,
            membership=membership,
            staff_role=self.role,
            employment_type=EmploymentType.FULL_TIME,
            hire_date=date.today(),
            base_salary=5000000,
            current_balance=2500000
        )
        
        response = self.client.get(f'{self.url}stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check summary stats
        self.assertIn('summary', response.data)
        summary = response.data['summary']
        self.assertEqual(summary['total_count'], 1)
        self.assertEqual(summary['active_count'], 1)
        self.assertEqual(summary['total_salary'], 5000000)
        
        # Check aggregations
        self.assertIn('by_employment_type', response.data)
        self.assertIn('by_role', response.data)
        self.assertIn('by_branch', response.data)

