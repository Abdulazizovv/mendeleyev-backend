from django.test import TestCase

from apps.branch.models import Branch, BranchMembership
from auth.users.models import User, UserBranch, BranchRole


class BranchMembershipProxyTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Alpha School", slug="alpha-school")
        self.user = User.objects.create_user(phone_number="+998901234567", password=None)

    def test_counts_match(self):
        # Initially empty
        self.assertEqual(BranchMembership.objects.count(), UserBranch.objects.count())
        # Create via proxy
        BranchMembership.objects.create(user=self.user, branch=self.branch, role=BranchRole.TEACHER)
        self.assertEqual(BranchMembership.objects.count(), UserBranch.objects.count())

    def test_crud_shared_table(self):
        # Create via proxy
        m = BranchMembership.objects.create(user=self.user, branch=self.branch, role=BranchRole.STUDENT, title="Learner")
        # Read via base
        m2 = UserBranch.objects.get(pk=m.pk)
        self.assertEqual(m2.role, BranchRole.STUDENT)
        self.assertEqual(m2.title, "Learner")
        # Update via base
        m2.title = "Senior Learner"
        m2.save()
        # Read via proxy
        m.refresh_from_db()
        self.assertEqual(m.title, "Senior Learner")
        # Soft delete via base reflects in proxy (record remains, deleted_at set)
        m2.delete()  # soft delete
        m.refresh_from_db()
        self.assertIsNotNone(m.deleted_at)
        self.assertEqual(BranchMembership.objects.count(), UserBranch.objects.count())
        # Hard delete to remove row
        m2.hard_delete()
        self.assertEqual(BranchMembership.objects.count(), 0)
