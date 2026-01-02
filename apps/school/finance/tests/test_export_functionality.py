"""
Export functionality testlari.
Excel export qilish va Celery task testlari.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status

from apps.branch.models import Branch, BranchMembership, BranchRole
from apps.school.finance.models import (
    CashRegister,
    FinanceCategory,
    Transaction,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
)

User = get_user_model()


class ExportFunctionalityTest(TestCase):
    """Export API va task testlari."""

    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        # Branch yaratish
        self.branch = Branch.objects.create(
            name="Test Branch",
            type="school",
            slug="test-branch",
            address="Test Address"
        )

        # User yaratish (Branch Admin)
        self.admin_user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123"
        )
        self.admin_membership = BranchMembership.objects.create(
            user=self.admin_user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
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

        # Tranzaksiyalar yaratish
        for i in range(5):
            Transaction.objects.create(
                branch=self.branch,
                cash_register=self.cash_register,
                transaction_type=TransactionType.INCOME,
                category=self.income_category,
                amount=100000 * (i + 1),
                payment_method=PaymentMethod.CASH,
                status=TransactionStatus.COMPLETED,
                description=f"Test Income {i+1}"
            )

        for i in range(3):
            Transaction.objects.create(
                branch=self.branch,
                cash_register=self.cash_register,
                transaction_type=TransactionType.EXPENSE,
                category=self.expense_category,
                amount=50000 * (i + 1),
                payment_method=PaymentMethod.CASH,
                status=TransactionStatus.COMPLETED,
                description=f"Test Expense {i+1}"
            )

        # API client
        self.client = APIClient()

    def test_export_transactions_starts_task(self):
        """Export tranzaksiyalar task boshlashi kerak."""
        self.client.force_authenticate(user=self.admin_user)

        with patch('apps.school.finance.tasks.export_transactions_to_excel.delay') as mock_task:
            # Mock task ID
            mock_task.return_value = MagicMock(id='test-task-id-123')

            response = self.client.post(
                '/api/v1/school/finance/export/transactions/',
                {},
                format='json',
                HTTP_X_BRANCH_ID=str(self.branch.id)
            )

            # Response tekshirish
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertIn('task_id', response.data)
            self.assertIn('message', response.data)
            self.assertEqual(response.data['status'], 'PENDING')

            # Task called bo'lganligini tekshirish
            mock_task.assert_called_once()
            call_kwargs = mock_task.call_args[1]
            self.assertEqual(call_kwargs['branch_id'], str(self.branch.id))
            self.assertEqual(call_kwargs['user_id'], str(self.admin_user.id))

    def test_export_transactions_with_filters(self):
        """Export tranzaksiyalar filtrlar bilan."""
        self.client.force_authenticate(user=self.admin_user)

        with patch('apps.school.finance.tasks.export_transactions_to_excel.delay') as mock_task:
            mock_task.return_value = MagicMock(id='test-task-id-456')

            data = {
                'transaction_type': TransactionType.INCOME,
                'status': TransactionStatus.COMPLETED,
                'date_from': '2025-01-01',
                'date_to': '2025-12-31',
            }

            response = self.client.post(
                '/api/v1/school/finance/export/transactions/',
                data,
                format='json',
                HTTP_X_BRANCH_ID=str(self.branch.id)
            )

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            # Task parametrlarini tekshirish
            call_kwargs = mock_task.call_args[1]
            self.assertIn('filters', call_kwargs)
            filters = call_kwargs['filters']
            self.assertEqual(filters['transaction_type'], TransactionType.INCOME)
            self.assertEqual(filters['status'], TransactionStatus.COMPLETED)
            self.assertEqual(filters['date_from'], '2025-01-01')
            self.assertEqual(filters['date_to'], '2025-12-31')

    def test_export_requires_authentication(self):
        """Export autentifikatsiya talab qiladi."""
        response = self.client.post(
            '/api/v1/school/finance/export/transactions/',
            {},
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_requires_branch_id(self):
        """Export branch_id talab qiladi (agar membership bo'lmasa)."""
        # Yangi user yaratish (membership yo'q)
        new_user = User.objects.create_user(
            phone_number="+998901234599",
            password="testpass123"
        )
        self.client.force_authenticate(user=new_user)

        response = self.client.post(
            '/api/v1/school/finance/export/transactions/',
            {},
            format='json'
            # No HTTP_X_BRANCH_ID and no membership
        )

        # Branch ID topilmasa, task qo'yilmaydi yoki 400 error qaytaradi
        # Ammo hozirgi kod membership dan branch_id ni topadi
        # Shuning uchun bu test membership yo'q user uchun 400 beradi
        self.assertTrue(
            response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
        )

    @patch('celery.result.AsyncResult')
    def test_task_status_pending(self, mock_async_result):
        """Task status PENDING."""
        self.client.force_authenticate(user=self.admin_user)

        # Mock task state
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_async_result.return_value = mock_task

        response = self.client.get(
            '/api/v1/school/finance/export/task-status/test-task-id-123/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertIn('message', response.data)

    @patch('celery.result.AsyncResult')
    def test_task_status_success(self, mock_async_result):
        """Task status SUCCESS va fayl URL qaytarishi kerak."""
        self.client.force_authenticate(user=self.admin_user)

        # Mock task result
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {
            'success': True,
            'file_url': '/media/exports/finance/transactions_20250102_143022.xlsx',
            'filename': 'transactions_20250102_143022.xlsx',
            'records_count': 523
        }
        mock_async_result.return_value = mock_task

        response = self.client.get(
            '/api/v1/school/finance/export/task-status/test-task-id-success/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertIn('file_url', response.data)
        self.assertIn('filename', response.data)
        self.assertIn('records_count', response.data)
        self.assertEqual(response.data['records_count'], 523)

    @patch('celery.result.AsyncResult')
    def test_task_status_failure(self, mock_async_result):
        """Task status FAILURE va error message."""
        self.client.force_authenticate(user=self.admin_user)

        # Mock task failure
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.info = Exception("Database connection error")
        mock_async_result.return_value = mock_task

        response = self.client.get(
            '/api/v1/school/finance/export/task-status/test-task-id-fail/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'FAILURE')
        self.assertIn('error', response.data)

    def test_export_task_creates_excel_file(self):
        """Export task Excel fayl yaratishi kerak (integration test)."""
        from apps.school.finance.tasks import export_transactions_to_excel

        # Task ni bevosita chaqirish (Celery eager mode)
        result = export_transactions_to_excel(
            branch_id=str(self.branch.id),
            filters={
                'transaction_type': TransactionType.INCOME
            },
            user_id=str(self.admin_user.id)
        )

        # Result tekshirish
        self.assertTrue(result['success'])
        self.assertIn('file_url', result)
        self.assertIn('filename', result)
        self.assertIn('records_count', result)
        self.assertEqual(result['records_count'], 5)  # 5 ta income transaction

    def test_export_task_with_no_records(self):
        """Export task ma'lumot yo'q bo'lsa xatolik qaytarishi kerak."""
        from apps.school.finance.tasks import export_transactions_to_excel

        # Boshqa branch uchun export (ma'lumot yo'q)
        other_branch = Branch.objects.create(
            name="Empty Branch",
            type="school",
            slug="empty-branch",
            address="Test"
        )

        result = export_transactions_to_excel(
            branch_id=str(other_branch.id),
            filters={},
            user_id=str(self.admin_user.id)
        )

        # Xatolik tekshirish
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('topilmadi', result['error'].lower())

    def test_export_task_applies_date_filter(self):
        """Export task sana filtrlarini to'g'ri qo'llashi kerak."""
        from apps.school.finance.tasks import export_transactions_to_excel
        from datetime import date, timedelta

        # Eski transaction yaratish
        old_transaction = Transaction.objects.create(
            branch=self.branch,
            cash_register=self.cash_register,
            transaction_type=TransactionType.INCOME,
            category=self.income_category,
            amount=999000,
            payment_method=PaymentMethod.CASH,
            status=TransactionStatus.COMPLETED,
            description="Old Transaction"
        )
        # Eski sana qo'yish
        old_date = date.today() - timedelta(days=365)
        Transaction.objects.filter(id=old_transaction.id).update(
            transaction_date=old_date
        )

        # Yangi sanadan export qilish
        result = export_transactions_to_excel(
            branch_id=str(self.branch.id),
            filters={
                'date_from': str(date.today() - timedelta(days=30))
            },
            user_id=str(self.admin_user.id)
        )

        self.assertTrue(result['success'])
        # Eski transaction export ga kirmasligi kerak (faqat oxirgi 30 kunlik)
        self.assertEqual(result['records_count'], 8)  # 5 income + 3 expense (hozirgi sanada)
