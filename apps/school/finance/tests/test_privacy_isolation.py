"""
Privacy va branch isolation testlari.
Har bir branch o'z ma'lumotlarigagina kirish huquqiga ega.
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.test import TestCase

from apps.branch.models import Branch, BranchMembership
from apps.school.finance.models import (
    CashRegister,
    Discount,
    FinanceCategory,
    Transaction,
)

User = get_user_model()


class BranchIsolationBasicTest(TestCase):
    """Branch isolation - har bir branch faqat o'z ma'lumotlarini ko'rishi."""

    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        # Ikki xil branch yaratish
        self.branch1 = Branch.objects.create(
            name='Branch 1',
            address='Address 1'
        )
        
        self.branch2 = Branch.objects.create(
            name='Branch 2',
            address='Address 2'
        )
        
        # Har bir branch uchun user va membership
        self.user1 = User.objects.create_user(
            phone_number='+998901111111',
            password='testpass123'
        )
        self.membership1 = BranchMembership.objects.create(
            user=self.user1,
            branch=self.branch1,
            role='branch_admin'
        )
        
        self.user2 = User.objects.create_user(
            phone_number='+998902222222',
            password='testpass123'
        )
        self.membership2 = BranchMembership.objects.create(
            user=self.user2,
            branch=self.branch2,
            role='branch_admin'
        )
        
        # Har bir branch uchun kassa
        self.cash_register1 = CashRegister.objects.create(
            name='Kassa 1',
            branch=self.branch1,
            balance=50000
        )
        
        self.cash_register2 = CashRegister.objects.create(
            name='Kassa 2',
            branch=self.branch2,
            balance=75000
        )
        
        # Har bir branch uchun kategoriya
        self.category1 = FinanceCategory.objects.create(
            name='Category 1',
            type='income',
            branch=self.branch1
        )
        
        self.category2 = FinanceCategory.objects.create(
            name='Category 2',
            type='expense',
            branch=self.branch2
        )
        
        # Global kategoriya
        self.global_category = FinanceCategory.objects.create(
            name='Global Category',
            type='income',
            branch=None
        )
        
        # Har bir branch uchun transaction
        self.transaction1 = Transaction.objects.create(
            branch=self.branch1,
            cash_register=self.cash_register1,
            category=self.category1,
            transaction_type='income',
            amount=5000,
            description='Transaction 1',
            created_by=self.user1
        )
        
        self.transaction2 = Transaction.objects.create(
            branch=self.branch2,
            cash_register=self.cash_register2,
            category=self.category2,
            transaction_type='expense',
            amount=3000,
            description='Transaction 2',
            created_by=self.user2
        )

    def test_transaction_queryset_filters_by_branch(self):
        """Transactionlar branch bo'yicha filtrlangan."""
        # Branch1 transactionlari
        branch1_transactions = Transaction.objects.filter(branch=self.branch1)
        self.assertEqual(branch1_transactions.count(), 1)
        self.assertIn(self.transaction1, branch1_transactions)
        self.assertNotIn(self.transaction2, branch1_transactions)

    def test_cash_register_queryset_filters_by_branch(self):
        """Cash register branch bo'yicha filtrlangan."""
        branch2_registers = CashRegister.objects.filter(branch=self.branch2)
        self.assertEqual(branch2_registers.count(), 1)
        self.assertIn(self.cash_register2, branch2_registers)
        self.assertNotIn(self.cash_register1, branch2_registers)

    def test_category_includes_branch_and_global(self):
        """Branch kategoriyalari + global kategoriyalar."""
        # Branch1 uchun: o'z kategoriyasi + global
        branch1_categories = FinanceCategory.objects.filter(
            models.Q(branch=self.branch1) | models.Q(branch__isnull=True)
        )
        
        self.assertIn(self.category1, branch1_categories)
        self.assertIn(self.global_category, branch1_categories)
        self.assertNotIn(self.category2, branch1_categories)

    def test_discount_branch_validation(self):
        """
        Discount faqat o'z branchida yoki global bo'lsa
        ishlashi kerak.
        """
        from django.db import models
        
        # Branch1 uchun discount
        discount1 = Discount.objects.create(
            name='Discount 1',
            discount_type='percentage',
            amount=10,
            branch=self.branch1,
            is_active=True
        )
        
        # Branch2 uchun discount
        discount2 = Discount.objects.create(
            name='Discount 2',
            discount_type='percentage',
            amount=15,
            branch=self.branch2,
            is_active=True
        )
        
        # Global discount
        global_discount = Discount.objects.create(
            name='Global Discount',
            discount_type='fixed',
            amount=5000,
            branch=None,
            is_active=True
        )
        
        # Branch1 uchun discount1 va global ishlashi kerak
        result1 = discount1.calculate_discount(10000, self.branch1)
        self.assertEqual(result1, 1000)
        
        result_global = global_discount.calculate_discount(10000, self.branch1)
        self.assertEqual(result_global, 5000)
        
        # Branch1 uchun discount2 (branch2 discount) ishlamasligi kerak
        result2 = discount2.calculate_discount(10000, self.branch1)
        self.assertEqual(result2, 0, "Cross-branch discount should not apply")
