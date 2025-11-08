from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.branch.models import Branch, BranchStatuses
from auth.users.models import UserBranch, BranchRole
from apps.common.otp import _get_store, _key_for_cooldown, _key_for_code, _key_for_attempts

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.phone_existing = "+998901112233"
        self.user_unverified = User.objects.create_user(phone_number=self.phone_existing)
        # By default: phone_verified=False, unusable password
        # Clear any OTP leftovers for this phone across purposes
        self._clear_otp_all(self.phone_existing)

    def _clear_otp(self, phone: str, purpose: str):
        r = _get_store()
        for key in (
            _key_for_cooldown(phone, purpose),
            _key_for_code(phone, purpose),
            _key_for_attempts(phone, purpose),
        ):
            try:
                r.delete(key)
            except Exception:
                pass

    def _clear_otp_all(self, phone: str):
        for purpose in ("generic", "verify", "reset", "register"):
            self._clear_otp(phone, purpose)

    def test_phone_check_unknown(self):
        url = reverse("auth-phone-check")
        res = self.client.post(url, {"phone_number": "+998901234567"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data.get("state"), "NOT_FOUND")

    def test_phone_check_existing_states(self):
        url = reverse("auth-phone-check")
        # Initially NOT_VERIFIED (unverified + no password)
        res1 = self.client.post(url, {"phone_number": self.phone_existing}, format="json")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.data.get("state"), "NOT_VERIFIED")

        # Verified but needs password
        self.user_unverified.phone_verified = True
        self.user_unverified.save(update_fields=["phone_verified"])
        res2 = self.client.post(url, {"phone_number": self.phone_existing}, format="json")
        self.assertEqual(res2.data.get("state"), "NEEDS_PASSWORD")

        # When password set -> READY
        self.user_unverified.set_password("StrongPassw0rd!")
        self.user_unverified.save()
        res3 = self.client.post(url, {"phone_number": self.phone_existing}, format="json")
        self.assertEqual(res3.data.get("state"), "READY")

    def test_phone_verification_request_and_confirm(self):
        # Ensure user is unverified
        self.user_unverified.phone_verified = False
        self.user_unverified.set_unusable_password()
        self.user_unverified.save()
        # ensure cooldown cleared for verify purpose
        self._clear_otp(self.phone_existing, "verify")

        # Request
        req_url = reverse("auth-phone-verification-request")
        res_req = self.client.post(req_url, {"phone_number": self.phone_existing}, format="json")
        self.assertEqual(res_req.status_code, 200)

        # Confirm (mock OTPService.verify_code)
        with patch("auth.users.views.OTPService.verify_code", return_value=True):
            conf_url = reverse("auth-phone-verification-confirm")
            res_conf = self.client.post(conf_url, {"phone_number": self.phone_existing, "code": "123456"}, format="json")
            self.assertEqual(res_conf.status_code, 200)
            self.user_unverified.refresh_from_db()
            self.assertTrue(self.user_unverified.phone_verified)

    def test_set_password_flow(self):
        # Verified but with unusable password
        self.user_unverified.phone_verified = True
        self.user_unverified.set_unusable_password()
        self.user_unverified.save()

        url = reverse("auth-password-set")
        res = self.client.post(url, {"phone_number": self.phone_existing, "password": "MyStr0ngPass!"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        # Now should be READY
        self.user_unverified.refresh_from_db()
        self.assertTrue(self.user_unverified.has_usable_password())

    def test_login_gating_and_success(self):
        login_url = reverse("auth-login")

        # Unverified
        self.user_unverified.phone_verified = False
        self.user_unverified.set_unusable_password()
        self.user_unverified.save()
        res_unver = self.client.post(login_url, {"phone_number": self.phone_existing, "password": "x"}, format="json")
        self.assertEqual(res_unver.status_code, 200)
        self.assertEqual(res_unver.data.get("state"), "NOT_VERIFIED")

        # Verified but no password
        self.user_unverified.phone_verified = True
        self.user_unverified.set_unusable_password()
        self.user_unverified.save()
        res_need = self.client.post(login_url, {"phone_number": self.phone_existing, "password": "x"}, format="json")
        self.assertEqual(res_need.status_code, 200)
        self.assertEqual(res_need.data.get("state"), "NEEDS_PASSWORD")

        # Wrong password
        self.user_unverified.set_password("CorrectPass123!")
        self.user_unverified.save()
        res_wrong = self.client.post(login_url, {"phone_number": self.phone_existing, "password": "Nope"}, format="json")
        self.assertEqual(res_wrong.status_code, 400)

        # Add active branch membership before expecting success
        b = Branch.objects.create(name="Test Branch", status=BranchStatuses.ACTIVE)
        UserBranch.objects.create(user=self.user_unverified, branch=b, role=BranchRole.TEACHER)
        res_ok = self.client.post(login_url, {"phone_number": self.phone_existing, "password": "CorrectPass123!"}, format="json")
        self.assertEqual(res_ok.status_code, 200)
        # For single branch user tokens should include br/br_role
        self.assertIn("access", res_ok.data)
        self.assertIn("refresh", res_ok.data)
        self.assertEqual(res_ok.data.get("br"), str(b.id))
        self.assertEqual(res_ok.data.get("br_role"), BranchRole.TEACHER)

    def test_password_reset_and_change(self):
        # Prepare user READY
        self.user_unverified.phone_verified = True
        self.user_unverified.set_password("OldPass123!")
        self.user_unverified.save()
        # ensure cooldown cleared for reset purpose
        self._clear_otp(self.phone_existing, "reset")

        # Request reset (always 200)
        reset_req_url = reverse("auth-password-reset-request")
        rr = self.client.post(reset_req_url, {"phone_number": self.phone_existing}, format="json")
        self.assertEqual(rr.status_code, 200)

        # Confirm reset (mock OTP verify)
        with patch("auth.users.views.OTPService.verify_code", return_value=True):
            reset_conf_url = reverse("auth-password-reset-confirm")
            rc = self.client.post(reset_conf_url, {"phone_number": self.phone_existing, "code": "123456", "new_password": "NewPass123!"}, format="json")
            self.assertEqual(rc.status_code, 200)
            self.assertIn("access", rc.data)
            self.assertIn("refresh", rc.data)

        # Auth and change password (use token from reset confirm, which is returned regardless of branch membership)
        token_from_reset = rc.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_from_reset}")

        ch = self.client.post(reverse("auth-password-change"), {"old_password": "NewPass123!", "new_password": "EvenNewer123!"}, format="json")
        self.assertEqual(ch.status_code, 200)

        # Need branch membership to login successfully (flow issues tokens regardless on password reset confirm)
        b = Branch.objects.create(name="Reset Branch", status=BranchStatuses.ACTIVE)
        UserBranch.objects.create(user=self.user_unverified, branch=b, role=BranchRole.TEACHER)
        # Login with new password works and returns scoped tokens
        self.client.credentials()  # reset
        login2 = self.client.post(reverse("auth-login"), {"phone_number": self.phone_existing, "password": "EvenNewer123!"}, format="json")
        self.assertEqual(login2.status_code, 200)
        self.assertIn("access", login2.data)
        self.assertEqual(login2.data.get("br"), str(b.id))
