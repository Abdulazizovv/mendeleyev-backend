import warnings
from django.test import TestCase

from apps.branch.models import Branch, BranchMembership
from auth.users.models import User, UserBranch, BranchRole


class LegacyUserBranchCompatTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Beta Center", slug="beta-center")
        self.user = User.objects.create_user(phone_number="+998998887766")

    def test_legacy_userbranch_still_queries_same_data(self):
        m = BranchMembership.objects.create(user=self.user, branch=self.branch, role=BranchRole.TEACHER)
        # Query via legacy model returns the same row
        self.assertTrue(UserBranch.objects.filter(pk=m.pk).exists())
        self.assertEqual(UserBranch.objects.count(), BranchMembership.objects.count())

    def test_deprecation_warning_on_userbranch_init(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # Constructing via legacy model should warn but still work
            legacy = UserBranch(user=self.user, branch=self.branch, role=BranchRole.STUDENT)
            self.assertTrue(any(issubclass(ww.category, DeprecationWarning) for ww in w))
            # Save and ensure visible via canonical class
            legacy.save()
            self.assertTrue(BranchMembership.objects.filter(pk=legacy.pk).exists())
