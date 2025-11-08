from django.urls import reverse
from django.test import TestCase, override_settings
from unittest.mock import patch
from rest_framework.test import APIClient
from apps.common.otp import OTPService


class AuthFlowTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.phone = "+998901234567"

	def test_request_otp_success(self):
		url = reverse("auth-request-otp")
		res = self.client.post(url, {"phone_number": self.phone}, format="json")
		self.assertEqual(res.status_code, 200)
		self.assertIn("expires_in", res.data)

	@override_settings(OTP_CODE_TTL_SECONDS=120)
	def test_verify_otp_and_issue_tokens(self):
		with patch.object(OTPService, "generate_code", return_value="111111"):
			# Request code (sets it to 111111)
			url_req = reverse("auth-request-otp")
			res1 = self.client.post(url_req, {"phone_number": self.phone}, format="json")
			self.assertEqual(res1.status_code, 200)

		# Verify
		url_ver = reverse("auth-verify-otp")
		res2 = self.client.post(url_ver, {"phone_number": self.phone, "code": "111111"}, format="json")
		self.assertEqual(res2.status_code, 200)
		self.assertIn("access", res2.data)
		self.assertIn("refresh", res2.data)
		self.assertIn("user", res2.data)

		# Access me
		token = res2.data["access"]
		self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
		url_me = reverse("auth-me")
		res3 = self.client.get(url_me)
		self.assertEqual(res3.status_code, 200)
		self.assertEqual(res3.data["phone_number"], self.phone)

