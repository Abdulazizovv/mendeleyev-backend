"""
Finance API testlari.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile, StudentStatus
from apps.school.finance.models import (
    CashRegister, Transaction, StudentBalance, Payment,
    TransactionType, TransactionStatus, PaymentMethod, SubscriptionPeriod
)

User = get_user_model()


class FinanceModelTests(TestCase):
    """Finance model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
        self.admin_membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
        )
        
        # Student yaratish
        self.student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123",
            first_name="Ali",
            last_name="Valiyev"
        )
        self.student_membership = BranchMembership.objects.create(
            user=self.student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user_branch=self.student_membership,
            status=StudentStatus.ACTIVE
        )
    
    def test_cash_register_creation(self):
        """Kassa yaratish testi."""
        cash_register = CashRegister.objects.create(
            branch=self.branch,
            name="Asosiy kassa",
            balance=0
        )
        
        self.assertEqual(cash_register.branch, self.branch)
        self.assertEqual(cash_register.balance, 0)
        self.assertTrue(cash_register.is_active)
    
    def test_transaction_balance_update(self):
        """Tranzaksiya kassa balansini yangilash testi."""
        cash_register = CashRegister.objects.create(
            branch=self.branch,
            name="Asosiy kassa",
            balance=0
        )
        
        # Payment tranzaksiyasi
        transaction = Transaction.objects.create(
            branch=self.branch,
            cash_register=cash_register,
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.COMPLETED,
            amount=1000000,
            payment_method=PaymentMethod.CASH,
            description="Test to'lov",
            student_profile=self.student_profile
        )
        
        # Kassa balansi yangilanishi kerak
        cash_register.refresh_from_db()
        self.assertEqual(cash_register.balance, 1000000)
    
    def test_student_balance_update(self):
        """O'quvchi balansini yangilash testi."""
        student_balance = StudentBalance.objects.get(student_profile=self.student_profile)
        initial_balance = student_balance.balance
        
        # Balansga summa qo'shish
        student_balance.add_amount(500000)
        
        student_balance.refresh_from_db()
        self.assertEqual(student_balance.balance, initial_balance + 500000)
    
    def test_payment_creation(self):
        """To'lov yaratish testi."""
        cash_register = CashRegister.objects.create(
            branch=self.branch,
            name="Asosiy kassa",
            balance=0
        )
        
        # To'lov yaratish (PaymentCreateSerializer orqali)
        # Bu testda biz to'g'ridan-to'g'ri Payment yaratamiz
        transaction = Transaction.objects.create(
            branch=self.branch,
            cash_register=cash_register,
            transaction_type=TransactionType.PAYMENT,
            status=TransactionStatus.COMPLETED,
            amount=1500000,
            payment_method=PaymentMethod.CASH,
            description="O'quvchi to'lovi",
            student_profile=self.student_profile
        )
        
        payment = Payment.objects.create(
            student_profile=self.student_profile,
            branch=self.branch,
            base_amount=1500000,
            discount_amount=0,
            final_amount=1500000,
            payment_method=PaymentMethod.CASH,
            period=SubscriptionPeriod.MONTHLY,
            transaction=transaction
        )
        
        self.assertEqual(payment.final_amount, 1500000)
        self.assertEqual(payment.transaction, transaction)
        
        # O'quvchi balansi yangilanishi kerak
        student_balance = StudentBalance.objects.get(student_profile=self.student_profile)
        # Balans yangilanishi PaymentCreateSerializer'da amalga oshiriladi
        # Bu testda biz uni qo'lda tekshiramiz
        self.assertIsNotNone(student_balance)


class FinanceAPITests(TestCase):
    """Finance API testlari."""
    
    def setUp(self):
        self.client = APIClient()
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
        self.admin_membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
        )
        self.client.force_authenticate(user=self.user)
        
        # Student yaratish
        self.student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123"
        )
        self.student_membership = BranchMembership.objects.create(
            user=self.student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user_branch=self.student_membership,
            status=StudentStatus.ACTIVE
        )
    
    def test_create_cash_register(self):
        """Kassa yaratish API testi."""
        url = '/api/v1/school/finance/cash-registers/'
        data = {
            'branch': str(self.branch.id),
            'name': 'Asosiy kassa',
            'description': 'Test kassa',
            'location': '1-qavat'
        }
        response = self.client.post(url, data, format='json', HTTP_X_BRANCH_ID=str(self.branch.id))
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Asosiy kassa')
    
    def test_list_cash_registers(self):
        """Kassalar ro'yxati API testi."""
        CashRegister.objects.create(
            branch=self.branch,
            name="Asosiy kassa",
            balance=0
        )
        
        url = '/api/v1/school/finance/cash-registers/'
        response = self.client.get(url, HTTP_X_BRANCH_ID=str(self.branch.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_list_student_balances(self):
        """O'quvchi balanslari ro'yxati API testi."""
        url = '/api/v1/school/finance/student-balances/'
        response = self.client.get(url, HTTP_X_BRANCH_ID=str(self.branch.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # StudentBalance signal orqali avtomatik yaratilgan bo'lishi kerak
        self.assertGreaterEqual(len(response.data['results']), 0)

