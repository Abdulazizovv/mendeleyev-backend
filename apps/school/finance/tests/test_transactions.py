"""
Tranzaksiya API testlari.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.finance.models import (
    CashRegister,
    Transaction,
    TransactionType,
    TransactionStatus,
    FinanceCategory,
    PaymentMethod,
)

User = get_user_model()


class TransactionAPITestCase(TestCase):
    """Tranzaksiya API testlari."""
    
    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        # Filial yaratish
        self.branch = Branch.objects.create(
            name="Test Filial",
            phone_number="+998901234567",
            address="Test address"
        )
        
        # Branch Admin yaratish
        self.admin_user = User.objects.create_user(
            phone_number="+998901111111",
            password="admin123",
            email="admin@test.com",
            first_name="Admin",
            last_name="User"
        )
        self.admin_membership = BranchMembership.objects.create(
            branch=self.branch,
            user=self.admin_user,
            role=BranchRole.BRANCH_ADMIN
        )
        
        # Super Admin yaratish
        self.super_admin = User.objects.create_superuser(
            phone_number="+998902222222",
            password="super123",
            email="super@test.com",
            first_name="Super",
            last_name="Admin"
        )
        self.super_membership = BranchMembership.objects.create(
            branch=self.branch,
            user=self.super_admin,
            role=BranchRole.SUPER_ADMIN
        )
        
        # Accountant yaratish
        self.accountant_user = User.objects.create_user(
            phone_number="+998903333333",
            password="acc123",
            email="acc@test.com",
            first_name="Accountant",
            last_name="User"
        )
        self.accountant_membership = BranchMembership.objects.create(
            branch=self.branch,
            user=self.accountant_user,
            role=BranchRole.OTHER
        )
        
        # Kassa yaratish
        self.cash_register = CashRegister.objects.create(
            branch=self.branch,
            name="Test Kassa",
            balance=5000000,  # 5 million
            is_active=True
        )
        
        # Kategoriyalar yaratish
        self.income_category = FinanceCategory.objects.create(
            branch=self.branch,
            type="income",
            name="O'quvchi to'lovi",
            is_active=True
        )
        self.expense_category = FinanceCategory.objects.create(
            branch=self.branch,
            type="expense",
            name="Xodim maoshi",
            is_active=True
        )
        
        # API client
        self.client = APIClient()
    
    def test_branch_admin_creates_income_auto_approved(self):
        """Branch Admin kirim yaratsa, avtomatik COMPLETED bo'lishi kerak."""
        self.client.force_authenticate(user=self.admin_user)
        
        initial_balance = self.cash_register.balance
        
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 500000,
            "payment_method": PaymentMethod.CASH,
            "description": "Test kirim"
        }
        
        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        print(f"\n=== RESPONSE STATUS: {response.status_code} ===")
        print(f"=== RESPONSE KEYS: {list(response.data.keys() if hasattr(response.data, 'keys') else [])} ===")
        print(f"=== RESPONSE DATA: {response.data} ===\n")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Status tekshirish
        if 'status' in response.data:
            self.assertEqual(response.data['status'], TransactionStatus.COMPLETED)
        
        # Kassa balansini tekshirish
        self.cash_register.refresh_from_db()
        expected_balance = initial_balance + 500000
        self.assertEqual(
            self.cash_register.balance,
            expected_balance,
            f"Kassa balansi {expected_balance} bo'lishi kerak, lekin {self.cash_register.balance}"
        )
    
    def test_branch_admin_creates_expense_auto_approved(self):
        """Branch Admin chiqim yaratsa, avtomatik COMPLETED bo'lishi kerak."""
        self.client.force_authenticate(user=self.admin_user)
        
        initial_balance = self.cash_register.balance
        
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.EXPENSE,
            "category": str(self.expense_category.id),
            "amount": 300000,
            "payment_method": PaymentMethod.CASH,
            "description": "Test chiqim"
        }
        
        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.COMPLETED)
        
        # Kassa balansini tekshirish
        self.cash_register.refresh_from_db()
        expected_balance = initial_balance - 300000
        self.assertEqual(
            self.cash_register.balance,
            expected_balance,
            f"Kassa balansi {expected_balance} bo'lishi kerak, lekin {self.cash_register.balance}"
        )
    
    def test_super_admin_creates_transaction_pending(self):
        """Super Admin tranzaksiya yaratsa, PENDING bo'lishi kerak."""
        self.client.force_authenticate(user=self.super_admin)
        
        initial_balance = self.cash_register.balance
        
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 500000,
            "payment_method": PaymentMethod.CASH,
            "description": "Super admin kirim"
        }
        
        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.PENDING)
        
        # Kassa balansi o'zgarmasligi kerak
        self.cash_register.refresh_from_db()
        self.assertEqual(
            self.cash_register.balance,
            initial_balance,
            "PENDING tranzaksiya kassa balansini o'zgartirmasligi kerak"
        )
    
    def test_accountant_creates_transaction_pending(self):
        """Accountant tranzaksiya yaratsa, PENDING bo'lishi kerak."""
        self.client.force_authenticate(user=self.accountant_user)
        
        initial_balance = self.cash_register.balance
        
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.income_category.id),
            "amount": 500000,
            "payment_method": PaymentMethod.CASH,
            "description": "Accountant kirim"
        }
        
        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], TransactionStatus.PENDING)
        
        # Kassa balansi o'zgarmasligi kerak
        self.cash_register.refresh_from_db()
        self.assertEqual(self.cash_register.balance, initial_balance)
    
    def test_insufficient_balance_for_expense(self):
        """Kassada mablag' yetarli bo'lmasa, xatolik berishi kerak."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.EXPENSE,
            "category": str(self.expense_category.id),
            "amount": 10000000,  # 10 million - kassada 5 million bor
            "payment_method": PaymentMethod.CASH,
            "description": "Katta chiqim"
        }
        
        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('amount', response.data)
    
    def test_category_type_mismatch(self):
        """Kategoriya turi tranzaksiya turiga mos kelmasa, xatolik berishi kerak."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            "cash_register": str(self.cash_register.id),
            "transaction_type": TransactionType.INCOME,
            "category": str(self.expense_category.id),  # Expense kategoriya income uchun
            "amount": 500000,
            "payment_method": PaymentMethod.CASH,
            "description": "Noto'g'ri kategoriya"
        }
        
        response = self.client.post(
            '/api/v1/school/finance/transactions/',
            data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)
    
    def test_multiple_transactions_balance_tracking(self):
        """Bir nechta tranzaksiya yaratilganda kassa balansi to'g'ri o'zgarishi kerak."""
        self.client.force_authenticate(user=self.admin_user)
        
        initial_balance = self.cash_register.balance  # 5000000
        
        # 1. Kirim +500000
        response1 = self.client.post(
            '/api/v1/school/finance/transactions/',
            {
                "cash_register": str(self.cash_register.id),
                "transaction_type": TransactionType.INCOME,
                "category": str(self.income_category.id),
                "amount": 500000,
                "payment_method": PaymentMethod.CASH,
                "description": "Kirim 1"
            },
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # 2. Chiqim -200000
        response2 = self.client.post(
            '/api/v1/school/finance/transactions/',
            {
                "cash_register": str(self.cash_register.id),
                "transaction_type": TransactionType.EXPENSE,
                "category": str(self.expense_category.id),
                "amount": 200000,
                "payment_method": PaymentMethod.CASH,
                "description": "Chiqim 1"
            },
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # 3. Kirim +300000
        response3 = self.client.post(
            '/api/v1/school/finance/transactions/',
            {
                "cash_register": str(self.cash_register.id),
                "transaction_type": TransactionType.INCOME,
                "category": str(self.income_category.id),
                "amount": 300000,
                "payment_method": PaymentMethod.CASH,
                "description": "Kirim 2"
            },
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        
        # Yakuniy balans: 5000000 + 500000 - 200000 + 300000 = 5600000
        self.cash_register.refresh_from_db()
        expected_balance = initial_balance + 500000 - 200000 + 300000
        self.assertEqual(
            self.cash_register.balance,
            expected_balance,
            f"Kassa balansi {expected_balance} bo'lishi kerak, lekin {self.cash_register.balance}"
        )
    
    def test_transaction_list_filtering(self):
        """Tranzaksiyalar ro'yxatini filtrlashtirish."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Kirim yaratish
        Transaction.objects.create(
            branch=self.branch,
            cash_register=self.cash_register,
            transaction_type=TransactionType.INCOME,
            category=self.income_category,
            amount=500000,
            status=TransactionStatus.COMPLETED
        )
        
        # Chiqim yaratish
        Transaction.objects.create(
            branch=self.branch,
            cash_register=self.cash_register,
            transaction_type=TransactionType.EXPENSE,
            category=self.expense_category,
            amount=200000,
            status=TransactionStatus.COMPLETED
        )
        
        # Faqat kirim
        response = self.client.get(
            '/api/v1/school/finance/transactions/?transaction_type=income',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        # Faqat chiqim
        response = self.client.get(
            '/api/v1/school/finance/transactions/?transaction_type=expense',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        
        # Barcha tranzaksiyalar
        response = self.client.get(
            '/api/v1/school/finance/transactions/',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
