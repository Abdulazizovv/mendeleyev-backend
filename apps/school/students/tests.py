"""
Students API testlari.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile, StudentRelative, RelativeType, StudentStatus
from apps.school.finance.models import StudentBalance

User = get_user_model()


class StudentModelTests(TestCase):
    """Student model testlari."""
    
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Test School",
            slug="test-school",
            type="school",
            status="active"
        )
        self.user = User.objects.create_user(
            phone_number="+998901234567",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        self.admin_membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.BRANCH_ADMIN
        )
    
    def test_student_profile_creation(self):
        """O'quvchi profili yaratish testi."""
        student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123",
            first_name="Ali",
            last_name="Valiyev"
        )
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        # StudentProfile signal orqali avtomatik yaratilishi mumkin
        student_profile, created = StudentProfile.objects.get_or_create(
            user_branch=student_membership,
            defaults={
                'middle_name': "Olim o'g'li",
                'gender': "male",
                'status': StudentStatus.ACTIVE
            }
        )
        
        # Agar allaqachon yaratilgan bo'lsa, ma'lumotlarni yangilaymiz
        if not created:
            student_profile.middle_name = "Olim o'g'li"
            student_profile.gender = "male"
            student_profile.status = StudentStatus.ACTIVE
            student_profile.save()
        
        self.assertEqual(student_profile.user_branch, student_membership)
        self.assertEqual(student_profile.gender, "male")
        self.assertEqual(student_profile.status, StudentStatus.ACTIVE)
        self.assertIsNotNone(student_profile.personal_number)
        
        # StudentBalance avtomatik yaratilishi kerak (signal orqali)
        self.assertTrue(StudentBalance.objects.filter(student_profile=student_profile).exists())
    
    def test_student_relative_creation(self):
        """O'quvchi yaqini yaratish testi."""
        student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123"
        )
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        student_profile = StudentProfile.objects.create(
            user_branch=student_membership
        )
        
        relative = StudentRelative.objects.create(
            student_profile=student_profile,
            relationship_type=RelativeType.FATHER,
            first_name="Olim",
            last_name="Valiyev",
            phone_number="+998901234569",
            is_primary_contact=True
        )
        
        self.assertEqual(relative.student_profile, student_profile)
        self.assertEqual(relative.relationship_type, RelativeType.FATHER)
        self.assertTrue(relative.is_primary_contact)


class StudentAPITests(TestCase):
    """Student API testlari."""
    
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
    
    def test_create_student(self):
        """O'quvchi yaratish API testi."""
        url = '/api/v1/school/students/create/'
        data = {
            'phone_number': '+998901234568',
            'first_name': 'Ali',
            'last_name': 'Valiyev',
            'branch_id': str(self.branch.id),
            'middle_name': "Olim o'g'li",
            'gender': 'male',
            'status': StudentStatus.ACTIVE
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['first_name'], 'Ali')
        
        # StudentProfile yaratilganligini tekshirish
        student_profile = StudentProfile.objects.filter(
            user_branch__user__phone_number='+998901234568'
        ).first()
        self.assertIsNotNone(student_profile)
    
    def test_list_students(self):
        """O'quvchilar ro'yxati API testi."""
        # Test o'quvchi yaratish
        student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123",
            first_name="Ali",
            last_name="Valiyev"
        )
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        StudentProfile.objects.create(
            user_branch=student_membership,
            status=StudentStatus.ACTIVE
        )
        
        url = '/api/v1/school/students/'
        response = self.client.get(url, {'branch_id': str(self.branch.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_user_check_api(self):
        """User tekshirish API testi."""
        # Test user yaratish
        student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123"
        )
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        StudentProfile.objects.create(
            user_branch=student_membership
        )
        
        url = '/api/v1/school/students/check-user/'
        response = self.client.get(url, {'phone_number': '+998901234568'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists_globally'])
        self.assertEqual(len(response.data['all_branches_data']), 1)
    
    def test_relative_check_api(self):
        """Relative tekshirish API testi."""
        # Test o'quvchi va yaqin yaratish
        student_user = User.objects.create_user(
            phone_number="+998901234568",
            password="testpass123"
        )
        student_membership = BranchMembership.objects.create(
            user=student_user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        student_profile = StudentProfile.objects.create(
            user_branch=student_membership
        )
        StudentRelative.objects.create(
            student_profile=student_profile,
            relationship_type=RelativeType.FATHER,
            first_name="Olim",
            last_name="Valiyev",
            phone_number="+998901234569"
        )
        
        url = '/api/v1/school/students/check-relative/'
        response = self.client.get(url, {'phone_number': '+998901234569'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists_globally'])
        self.assertEqual(len(response.data['all_branches_data']), 1)

