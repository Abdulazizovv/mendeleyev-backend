from django.test import TestCase

from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.users.models import User


class BranchMembershipTests(TestCase):
    """Tests for BranchMembership model."""
    
    def setUp(self):
        self.branch = Branch.objects.create(name="Alpha School", slug="alpha-school")
        self.user = User.objects.create_user(phone_number="+998901234567", password=None)

    def test_create_membership(self):
        """Test creating a membership."""
        membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER,
            title="Math Teacher"
        )
        self.assertEqual(membership.role, BranchRole.TEACHER)
        self.assertEqual(membership.title, "Math Teacher")
        self.assertEqual(BranchMembership.objects.count(), 1)

    def test_unique_together(self):
        """Test that user-branch combination is unique."""
        BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER
        )
        # Try to create duplicate
        with self.assertRaises(Exception):  # IntegrityError
            BranchMembership.objects.create(
                user=self.user,
                branch=self.branch,
                role=BranchRole.STUDENT
            )

    def test_soft_delete(self):
        """Test soft delete functionality."""
        membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.STUDENT,
            title="Learner"
        )
        membership.delete()  # soft delete
        membership.refresh_from_db()
        self.assertIsNotNone(membership.deleted_at)
        # Should still exist in database
        self.assertEqual(BranchMembership.objects.count(), 1)
        # But not in active queryset
        self.assertEqual(BranchMembership.objects.active().count(), 0)

    def test_hard_delete(self):
        """Test hard delete functionality."""
        membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.STUDENT
        )
        membership.hard_delete()
        self.assertEqual(BranchMembership.objects.count(), 0)

    def test_for_user_and_branch(self):
        """Test for_user_and_branch class method."""
        membership = BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER
        )
        found = BranchMembership.for_user_and_branch(self.user.id, self.branch.id)
        self.assertEqual(found, membership)

    def test_has_role(self):
        """Test has_role class method."""
        BranchMembership.objects.create(
            user=self.user,
            branch=self.branch,
            role=BranchRole.TEACHER
        )
        # Check with correct role
        self.assertTrue(BranchMembership.has_role(self.user.id, self.branch.id, [BranchRole.TEACHER]))
        # Check with wrong role
        self.assertFalse(BranchMembership.has_role(self.user.id, self.branch.id, [BranchRole.STUDENT]))
        # Check with any role
        self.assertTrue(BranchMembership.has_role(self.user.id, self.branch.id, None))
