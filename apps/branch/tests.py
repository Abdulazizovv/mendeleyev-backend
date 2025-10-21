from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.branch.models import Branch, BranchTypes, BranchStatuses


class BranchModelTests(TestCase):
	def test_queryset_helpers(self):
		Branch.objects.create(name='A1', type=BranchTypes.SCHOOL, status=BranchStatuses.ACTIVE)
		Branch.objects.create(name='B1', type=BranchTypes.CENTER, status=BranchStatuses.INACTIVE)

		self.assertEqual(Branch.objects.schools().count(), 1)
		self.assertEqual(Branch.objects.centers().count(), 1)
		self.assertEqual(Branch.objects.status_active().count(), 1)
		self.assertEqual(Branch.objects.status_inactive().count(), 1)

	def test_phone_validator(self):
		b = Branch(name='Valid', phone_number='+998901234567')
		# Should not raise on clean
		b.full_clean()

		b2 = Branch(name='Invalid', phone_number='abc123')
		with self.assertRaises(ValidationError):
			b2.full_clean()
