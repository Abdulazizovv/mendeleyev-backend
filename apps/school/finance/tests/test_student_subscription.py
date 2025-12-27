"""
StudentSubscription va Payment Due Summary API testlari.

Bu testlar:
1. StudentSubscription yaratish
2. To'lov xulosasini olish
3. Qarz hisoblash
4. Kechikkan oylarni hisoblash
"""
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile
from apps.school.finance.models import (
    StudentSubscription,
    SubscriptionPlan,
    SubscriptionPeriod,
)

User = get_user_model()


class TestStudentSubscriptionAPI(APITestCase):
    """StudentSubscription API testlari."""

    def setUp(self):
        """Test ma'lumotlarini tayyorlash."""
        # Branch
        self.branch = Branch.objects.create(
            name="Test Branch",
            address="Test Address"
        )
        
        # Super Admin
        self.admin_user = User.objects.create_user(
            phone_number="+998901234567",
            first_name="Admin",
            last_name="User"
        )
        self.admin_membership = BranchMembership.objects.create(
            user=self.admin_user,
            branch=self.branch,
            role=BranchRole.SUPER_ADMIN
        )
        
        # Student
        self.student_user = User.objects.create_user(
            phone_number="+998901234568",
            first_name="Ali",
            last_name="Valiyev"
        )
        self.student_membership = BranchMembership.objects.create(
            user=self.student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        # StudentProfile signal orqali avtomatik yaratiladi
        self.student_profile = StudentProfile.objects.get(user_branch=self.student_membership)
        self.student_profile.middle_name = "Aliyevich"
        self.student_profile.save()
        
        # Subscription Plan
        self.plan = SubscriptionPlan.objects.create(
            name="5-sinf (oylik)",
            price=500000,
            period=SubscriptionPeriod.MONTHLY,
            grade_level_min=5,
            grade_level_max=5,
            branch=self.branch
        )
        
        # API Client
        self.client.force_authenticate(user=self.admin_user)

    def test_create_subscription(self):
        """Abonement yaratish testi."""
        data = {
            'student_profile': str(self.student_profile.id),
            'subscription_plan': str(self.plan.id),
            'branch': str(self.branch.id),
            'start_date': '2025-01-01',
            'next_payment_date': '2025-02-01',
        }
        
        response = self.client.post(
            '/api/v1/school/finance/student-subscriptions/',
            data=data,
            format='json',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subscription_plan_name'], "5-sinf (oylik)")
        self.assertEqual(response.data['subscription_plan_price'], 500000)
        self.assertTrue(response.data['is_active'])
        self.assertEqual(response.data['total_debt'], 0)

    def test_payment_due_no_debt(self):
        """Qarzsiz to'lov xulosasi."""
        # Abonement yaratish
        subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            total_debt=0
        )
        
        response = self.client.get(
            f'/api/v1/school/finance/payment-due-summary/?student_profile_id={self.student_profile.id}',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        result = response.data[0]
        self.assertEqual(result['current_amount'], 500000)
        self.assertEqual(result['debt_amount'], 0)
        self.assertEqual(result['total_amount'], 500000)
        self.assertEqual(result['overdue_months'], 0)
        self.assertFalse(result['is_overdue'])

    def test_payment_due_with_debt(self):
        """Qarzli to'lov xulosasi."""
        # Kechikkan to'lov (2 oy oldin)
        next_due = date.today() - relativedelta(months=2)
        
        subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            start_date=date.today() - relativedelta(months=3),
            next_payment_date=next_due,
            total_debt=1000000,  # 2 oylik qarz
        )
        
        response = self.client.get(
            f'/api/v1/school/finance/payment-due-summary/?student_profile_id={self.student_profile.id}',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data[0]
        
        self.assertEqual(result['current_amount'], 500000)  # Joriy oy
        self.assertEqual(result['debt_amount'], 1000000)    # Qarz
        self.assertEqual(result['total_amount'], 1500000)   # Jami
        self.assertGreaterEqual(result['overdue_months'], 2)  # 2+ oy kechikkan
        self.assertTrue(result['is_overdue'])

    def test_calculate_payment_due_method(self):
        """calculate_payment_due() metodini test qilish."""
        # 1 oy kechikkan
        next_due = date.today() - relativedelta(months=1)
        
        subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            start_date=date.today() - relativedelta(months=2),
            next_payment_date=next_due,
            total_debt=500000,  # 1 oylik qarz
        )
        
        payment_due = subscription.calculate_payment_due()
        
        self.assertEqual(payment_due['current_amount'], 500000)
        self.assertEqual(payment_due['debt_amount'], 500000)
        self.assertEqual(payment_due['total_amount'], 1000000)
        self.assertGreaterEqual(payment_due['overdue_months'], 1)
        self.assertFalse(payment_due['is_expired'])

    def test_no_active_subscription(self):
        """Faol abonement yo'q testi."""
        response = self.client.get(
            f'/api/v1/school/finance/payment-due-summary/?student_profile_id={self.student_profile.id}',
            HTTP_X_BRANCH_ID=str(self.branch.id)
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('faol abonement topilmadi', response.data['error'].lower())

    def test_add_and_reduce_debt(self):
        """Qarz qo'shish va kamaytirish."""
        subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            start_date=date.today(),
            next_payment_date=date.today() + timedelta(days=30),
            total_debt=0
        )
        
        # Qarz qo'shish
        subscription.add_debt(500000)
        self.assertEqual(subscription.total_debt, 500000)
        
        # Yana qo'shish
        subscription.add_debt(500000)
        self.assertEqual(subscription.total_debt, 1000000)
        
        # Kamaytirish
        subscription.reduce_debt(300000)
        self.assertEqual(subscription.total_debt, 700000)

    def test_update_next_payment_date(self):
        """Keyingi to'lov sanasini yangilash."""
        subscription = StudentSubscription.objects.create(
            student_profile=self.student_profile,
            subscription_plan=self.plan,
            branch=self.branch,
            start_date=date(2025, 1, 1),
            next_payment_date=date(2025, 2, 1),
            total_debt=0
        )
        
        # Yangilash
        subscription.update_next_payment_date()
        
        # 1 oy qo'shilishi kerak
        self.assertEqual(subscription.next_payment_date, date(2025, 3, 1))
