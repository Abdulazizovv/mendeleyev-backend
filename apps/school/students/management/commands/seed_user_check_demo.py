from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.branch.models import Branch, BranchMembership, BranchRole
from auth.profiles.models import StudentProfile, StudentRelative, RelativeType


User = get_user_model()


class Command(BaseCommand):
    help = "User/Student/Relative check API larini test qilish uchun demo ma'lumotlar yaratadi."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Seed user-check demo data ==="))

        # 1. Filiallar
        branch1, _ = Branch.objects.get_or_create(
            name="Test Branch 1",
            defaults={"address": "Test address 1"},
        )
        branch2, _ = Branch.objects.get_or_create(
            name="Test Branch 2",
            defaults={"address": "Test address 2"},
        )

        # 2. Asosiy test user (siz ishlatayotgan raqam)
        main_phone = "+998331112234"
        user, _ = User.objects.get_or_create(
            phone_number=main_phone,
            defaults={
                "first_name": "Test",
                "last_name": "Student",
            },
        )

        # 3. BranchMembership + StudentProfile (branch1)
        m1, _ = BranchMembership.objects.get_or_create(
            user=user,
            branch=branch1,
            role=BranchRole.STUDENT,
        )
        student1, _ = StudentProfile.objects.get_or_create(
            user_branch=m1,
            defaults={
                "middle_name": "",
                "gender": "unspecified",
                "date_of_birth": timezone.now().date(),
                "address": "Test address",
            },
        )

        # 4. Shu userni boshqa filialda ham bog'lab qo'yish (branch2)
        m2, _ = BranchMembership.objects.get_or_create(
            user=user,
            branch=branch2,
            role=BranchRole.STUDENT,
        )
        StudentProfile.objects.get_or_create(
            user_branch=m2,
            defaults={
                "middle_name": "",
                "gender": "unspecified",
                "date_of_birth": timezone.now().date(),
                "address": "Test address 2",
            },
        )

        # 5. Relative-lar (o'quvchi yaqinlari)
        relative_phone = "+998901234567"
        relative, _ = StudentRelative.objects.get_or_create(
            student_profile=student1,
            phone_number=relative_phone,
            defaults={
                "first_name": "Parent",
                "last_name": "One",
                "relationship_type": RelativeType.GUARDIAN,
                "is_primary_contact": True,
                "is_guardian": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar yaratildi:"))
        self.stdout.write(f"  - Branch 1 ID: {branch1.id} (Test Branch 1)")
        self.stdout.write(f"  - Branch 2 ID: {branch2.id} (Test Branch 2)")
        self.stdout.write(f"  - User phone: {user.phone_number}")
        self.stdout.write(f"  - Student 1 ID (branch1): {student1.id}")
        self.stdout.write(f"  - Relative phone: {relative.phone_number} (StudentRelative)")

        self.stdout.write("")
        self.stdout.write("Endi test qilishingiz mumkin:")
        self.stdout.write(f"  - GET /api/v1/school/students/check-user/?phone_number={main_phone}")
        self.stdout.write("  - yoki POST JSON {\"phone_number\": \"+998331112234\"}")
        self.stdout.write(f"  - Relative tekshiruv: /api/v1/school/students/check-relative/?phone_number={relative_phone}")


