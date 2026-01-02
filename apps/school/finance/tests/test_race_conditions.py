"""
Race condition va concurrency testlari.
StudentBalance operatsiyalarini parallel bajarilishda tekshirish.
"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TransactionTestCase

from apps.branch.models import Branch, BranchMembership
from apps.school.finance.models import (
    CashRegister,
    FinanceCategory,
    StudentBalance,
    Transaction,
)
from auth.profiles.models import StudentProfile

User = get_user_model()


class StudentBalanceRaceConditionTest(TransactionTestCase):
    """
    StudentBalance add_amount va subtract_amount metodlarini
    parallel bajarilishda race condition tekshirish.
    
    TransactionTestCase ishlatiladi chunki har bir thread
    o'z database connection ochishi kerak.
    """

    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        # User yaratish
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='testpass123'
        )
        
        # Branch yaratish
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='Test Address'
        )
        
        # BranchMembership yaratish (StudentProfile uchun kerak)
        self.membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role='student'
        )
        
        # StudentProfile olish (signal orqali avtomatik yaratilgan bo'lishi mumkin)
        self.student_profile, _ = StudentProfile.objects.get_or_create(
            user_branch=self.membership
        )
        
        # StudentBalance yaratish yoki olish
        self.student_balance, _ = StudentBalance.objects.get_or_create(
            student_profile=self.student_profile,
            defaults={'balance': 0}
        )

    def test_concurrent_add_amount(self):
        """
        Bir vaqtning o'zida ko'plab add_amount() chaqiruvlari
        to'g'ri ishlashini tekshirish.
        """
        num_threads = 10
        amount_per_thread = 1000
        expected_final_balance = num_threads * amount_per_thread

        def add_balance(balance_id):
            """Thread ichida balansga pul qo'shish."""
            balance = StudentBalance.objects.get(id=balance_id)
            balance.add_amount(amount_per_thread)
            return True

        # Parallel bajarish
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(add_balance, self.student_balance.id)
                for _ in range(num_threads)
            ]
            
            # Barcha threadlar tugashini kutish
            results = [future.result() for future in as_completed(futures)]
            
        # Yakuniy balansni tekshirish
        self.student_balance.refresh_from_db()
        self.assertEqual(
            self.student_balance.balance,
            expected_final_balance,
            f"Balance should be {expected_final_balance} after {num_threads} concurrent additions"
        )

    def test_concurrent_subtract_amount(self):
        """
        Bir vaqtning o'zida ko'plab subtract_amount() chaqiruvlari
        to'g'ri ishlashini va manfiy balansga yo'l qo'ymasligini tekshirish.
        """
        # Dastlab balansga pul qo'shish
        initial_balance = 10000
        self.student_balance.add_amount(initial_balance)
        
        num_threads = 20
        amount_per_thread = 600
        successful_subtractions = 0

        def subtract_balance(balance_id):
            """Thread ichida balansdan pul ayirish."""
            try:
                balance = StudentBalance.objects.get(id=balance_id)
                balance.subtract_amount(amount_per_thread)
                return True
            except ValueError:
                # Balans yetarli emas
                return False

        # Parallel bajarish
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(subtract_balance, self.student_balance.id)
                for _ in range(num_threads)
            ]
            
            # Natijalarni yig'ish
            for future in as_completed(futures):
                if future.result():
                    successful_subtractions += 1

        # Yakuniy balansni tekshirish
        self.student_balance.refresh_from_db()
        expected_balance = initial_balance - (successful_subtractions * amount_per_thread)
        
        self.assertEqual(
            self.student_balance.balance,
            expected_balance,
            f"Balance calculation mismatch: expected {expected_balance}, got {self.student_balance.balance}"
        )
        
        # Balans hech qachon manfiy bo'lmasligi kerak
        self.assertGreaterEqual(
            self.student_balance.balance,
            0,
            "Balance should never be negative"
        )

    def test_concurrent_mixed_operations(self):
        """
        Add va subtract operatsiyalarini aralash holda parallel bajarish.
        """
        initial_balance = 50000
        self.student_balance.add_amount(initial_balance)
        
        num_operations = 50
        add_amount = 1000
        subtract_amount = 800

        def mixed_operation(balance_id, operation_type):
            """Add yoki subtract operatsiyasini bajarish."""
            try:
                balance = StudentBalance.objects.get(id=balance_id)
                if operation_type == 'add':
                    balance.add_amount(add_amount)
                    return ('add', True)
                else:
                    balance.subtract_amount(subtract_amount)
                    return ('subtract', True)
            except ValueError:
                return ('subtract', False)

        # Parallel bajarish (yarmi add, yarmi subtract)
        operations = ['add'] * (num_operations // 2) + ['subtract'] * (num_operations // 2)
        results = {'add': 0, 'subtract': 0}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(mixed_operation, self.student_balance.id, op)
                for op in operations
            ]
            
            for future in as_completed(futures):
                op_type, success = future.result()
                if success:
                    results[op_type] += 1

        # Yakuniy balansni tekshirish
        self.student_balance.refresh_from_db()
        expected_balance = (
            initial_balance +
            (results['add'] * add_amount) -
            (results['subtract'] * subtract_amount)
        )
        
        self.assertEqual(
            self.student_balance.balance,
            expected_balance,
            f"Balance mismatch after mixed operations: expected {expected_balance}, got {self.student_balance.balance}"
        )
        
        self.assertGreaterEqual(self.student_balance.balance, 0)


class TransactionAtomicityTest(TransactionTestCase):
    """Transaction yaratishda atomicity va rollback tekshirish."""

    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        self.user = User.objects.create_user(
            phone_number='+998901234568',
            password='testpass123'
        )
        
        self.branch = Branch.objects.create(
            name='Test Branch',
            address='Test Address'
        )
        
        self.cash_register = CashRegister.objects.create(
            name='Test Kassa',
            branch=self.branch,
            balance=100000
        )
        
        self.category = FinanceCategory.objects.create(
            name='Test Category',
            type='income',
            branch=self.branch
        )

    def test_transaction_rollback_on_error(self):
        """
        Transaction yaratishda xatolik yuz berganda
        barcha o'zgarishlar bekor qilinishini tekshirish.
        """
        initial_cash_balance = self.cash_register.balance
        
        try:
            with transaction.atomic():
                # Transaction yaratish
                trans = Transaction.objects.create(
                    branch=self.branch,
                    cash_register=self.cash_register,
                    category=self.category,
                    transaction_type='income',
                    amount=5000,
                    description='Test transaction',
                    created_by=self.user
                )
                
                # Kassa balansini o'zgartirish
                self.cash_register.balance += 5000
                self.cash_register.save()
                
                # Tasodifiy xatolik chiqarish
                raise ValueError("Intentional error for rollback test")
                
        except ValueError:
            pass
        
        # Kassa balansi o'zgarmagan bo'lishi kerak
        self.cash_register.refresh_from_db()
        self.assertEqual(
            self.cash_register.balance,
            initial_cash_balance,
            "Cash register balance should rollback on transaction error"
        )
        
        # Transaction yaratilmagan bo'lishi kerak
        self.assertEqual(
            Transaction.objects.filter(description='Test transaction').count(),
            0,
            "Transaction should not exist after rollback"
        )

    def test_concurrent_cash_register_updates(self):
        """
        Bir vaqtning o'zida bir xil kassaga ko'plab
        transaction yaratilganda race condition bo'lmasligi.
        """
        num_transactions = 20
        amount_per_transaction = 1000
        
        def create_transaction(cash_register_id):
            """Thread ichida transaction yaratish."""
            try:
                with transaction.atomic():
                    cash_register = CashRegister.objects.select_for_update().get(id=cash_register_id)
                    
                    Transaction.objects.create(
                        branch=self.branch,
                        cash_register=cash_register,
                        category=self.category,
                        transaction_type='income',
                        amount=amount_per_transaction,
                        description=f'Concurrent transaction {threading.current_thread().name}',
                        created_by=self.user,
                        status='approved'
                    )
                    
                    cash_register.balance += amount_per_transaction
                    cash_register.save()
                    
                return True
            except Exception as e:
                print(f"Error in thread: {e}")
                return False

        initial_balance = self.cash_register.balance
        
        # Parallel bajarish
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(create_transaction, self.cash_register.id)
                for _ in range(num_transactions)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        successful_count = sum(results)
        
        # Kassa balansini tekshirish
        self.cash_register.refresh_from_db()
        expected_balance = initial_balance + (successful_count * amount_per_transaction)
        
        self.assertEqual(
            self.cash_register.balance,
            expected_balance,
            f"Cash register balance mismatch after concurrent transactions"
        )
        
        # Transaction sonini tekshirish
        created_transactions = Transaction.objects.filter(
            cash_register=self.cash_register,
            description__startswith='Concurrent transaction'
        ).count()
        
        self.assertEqual(
            created_transactions,
            successful_count,
            "Number of created transactions should match successful operations"
        )
