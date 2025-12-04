import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.branch.models import Branch, BranchMembership
from apps.school.classes.models import Class, ClassStudent

@pytest.mark.django_db
class TestClassStudentTransfer:
    def setup_method(self):
        self.client = APIClient()

    def test_transfer_student_success(self, django_user_model):
        # Setup branch, user, memberships and classes
        branch = Branch.objects.create(name="Main")
        user = django_user_model.objects.create_user(phone_number="+998901234567", password="pass")
        membership = BranchMembership.objects.create(branch=branch, user=user, role='student')

        ay = branch.academicyear_set.create(name="2024-2025")
        class_a = Class.objects.create(branch=branch, academic_year=ay, name="A")
        class_b = Class.objects.create(branch=branch, academic_year=ay, name="B")

        cs = ClassStudent.objects.create(class_obj=class_a, membership=membership)

        url = reverse('classes:class-student-transfer', kwargs={'class_id': str(class_a.id), 'student_id': str(membership.id)})
        resp = self.client.post(url, data={
            'target_class_id': str(class_b.id),
            'notes': 'Transfer test'
        }, format='json')
        assert resp.status_code == 201
        assert resp.data['class_obj'] == str(class_b.id)
        assert resp.data['membership_id'] == str(membership.id)

        # Old enrollment should be soft-deleted
        assert ClassStudent.objects.filter(class_obj=class_a, membership=membership, deleted_at__isnull=True).count() == 0
        assert ClassStudent.objects.filter(class_obj=class_b, membership=membership, deleted_at__isnull=True).count() == 1

    def test_transfer_student_already_in_target(self, django_user_model):
        branch = Branch.objects.create(name="Main")
        user = django_user_model.objects.create_user(phone_number="+998901234567", password="pass")
        membership = BranchMembership.objects.create(branch=branch, user=user, role='student')
        ay = branch.academicyear_set.create(name="2024-2025")
        class_a = Class.objects.create(branch=branch, academic_year=ay, name="A")
        class_b = Class.objects.create(branch=branch, academic_year=ay, name="B")
        ClassStudent.objects.create(class_obj=class_a, membership=membership)
        ClassStudent.objects.create(class_obj=class_b, membership=membership)

        url = reverse('classes:class-student-transfer', kwargs={'class_id': str(class_a.id), 'student_id': str(membership.id)})
        resp = self.client.post(url, data={'target_class_id': str(class_b.id)}, format='json')
        assert resp.status_code == 400
        assert 'Student already enrolled in target class' in str(resp.data)

    def test_transfer_student_different_branch(self, django_user_model):
        branch1 = Branch.objects.create(name="Main")
        branch2 = Branch.objects.create(name="Second")
        user = django_user_model.objects.create_user(phone_number="+998901234567", password="pass")
        membership = BranchMembership.objects.create(branch=branch1, user=user, role='student')
        ay1 = branch1.academicyear_set.create(name="2024-2025")
        ay2 = branch2.academicyear_set.create(name="2024-2025")
        class_a = Class.objects.create(branch=branch1, academic_year=ay1, name="A")
        class_b = Class.objects.create(branch=branch2, academic_year=ay2, name="B")
        ClassStudent.objects.create(class_obj=class_a, membership=membership)

        url = reverse('classes:class-student-transfer', kwargs={'class_id': str(class_a.id), 'student_id': str(membership.id)})
        resp = self.client.post(url, data={'target_class_id': str(class_b.id)}, format='json')
        assert resp.status_code == 400
        assert 'same branch' in str(resp.data)
