from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from apps.branch.models import Branch, BranchStatuses
from auth.users.models import UserBranch

User = get_user_model()

class RefreshTokenViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _post_refresh(self, refresh_str: str):
        return self.client.post('/api/v1/auth/refresh/', {"refresh": refresh_str}, format='json')

    def test_refresh_success_with_active_membership(self):
        user = User.objects.create_user(phone_number='+998931111111', password='Passw0rd!')
        branch = Branch.objects.create(name='Active Branch', status=BranchStatuses.ACTIVE)
        UserBranch.objects.create(user=user, branch=branch, role='teacher', title='Math Teacher')
        token = RefreshToken.for_user(user)
        token['br'] = str(branch.id)
        token['br_role'] = 'teacher'
        resp = self._post_refresh(str(token))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('access', data)
        # Decode new access token to verify claims
        new_refresh = RefreshToken(data['refresh'])
        access = new_refresh.access_token
        self.assertEqual(access.get('br'), str(branch.id))
        self.assertEqual(access.get('br_role'), 'teacher')

    def test_refresh_membership_not_found(self):
        user = User.objects.create_user(phone_number='+998932222222', password='Passw0rd!')
        branch = Branch.objects.create(name='Orphan Branch', status=BranchStatuses.ACTIVE)
        # No membership created
        token = RefreshToken.for_user(user)
        token['br'] = str(branch.id)
        resp = self._post_refresh(str(token))
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json().get('code'), 'membership_not_found')

    def test_refresh_branch_inactive(self):
        user = User.objects.create_user(phone_number='+998933333333', password='Passw0rd!')
        branch = Branch.objects.create(name='Inactive Branch', status=BranchStatuses.INACTIVE)
        UserBranch.objects.create(user=user, branch=branch, role='student', title='9A Student')
        token = RefreshToken.for_user(user)
        token['br'] = str(branch.id)
        token['br_role'] = 'student'
        resp = self._post_refresh(str(token))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json().get('code'), 'branch_inactive')

    def test_refresh_superuser_bypass(self):
        admin = User.objects.create_superuser(phone_number='+998934444444', password='Adm1nPass!')
        branch = Branch.objects.create(name='Inactive But Allowed', status=BranchStatuses.INACTIVE)
        token = RefreshToken.for_user(admin)
        token['br'] = str(branch.id)
        token['br_role'] = 'super_admin'
        resp = self._post_refresh(str(token))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        new_refresh = RefreshToken(data['refresh'])
        access = new_refresh.access_token
        self.assertEqual(access.get('br'), str(branch.id))
        self.assertEqual(access.get('br_role'), 'super_admin')
