from __future__ import annotations

from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from apps.common.models import BaseModel


class Gender(models.TextChoices):
	MALE = 'male', 'Male'
	FEMALE = 'female', 'Female'
	OTHER = 'other', 'Other'
	UNSPECIFIED = 'unspecified', 'Unspecified'


class Profile(BaseModel):
	"""Global profile for a user, independent of branch/role."""

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
	date_of_birth = models.DateField(blank=True, null=True)
	gender = models.CharField(max_length=16, choices=Gender.choices, default=Gender.UNSPECIFIED)
	language = models.CharField(max_length=16, default='uz', blank=True)
	timezone = models.CharField(max_length=64, default='Asia/Tashkent', blank=True)
	bio = models.TextField(blank=True, default='')
	address = models.CharField(max_length=255, blank=True, default='')
	socials = models.JSONField(blank=True, null=True, help_text='{"telegram":"@user", "instagram":"u"}')

	class Meta:
		verbose_name = 'Profil'
		verbose_name_plural = 'Profillar'

	def __str__(self):  # pragma: no cover - trivial
		return f"Profile<{self.user_id}>"



class UserBranchProfile(BaseModel):
	"""Backward-compatible generic role-aware profile.

	Phase 1: Keep this model for existing code (display_name/title/about), while we add
	new specialized per-role profile models below. Future phases may deprecate this.
	"""

	user_branch = models.OneToOneField('branch.BranchMembership', on_delete=models.CASCADE, related_name='generic_profile')
	display_name = models.CharField(max_length=150, blank=True, default='', help_text='Role-specific display name')
	title = models.CharField(max_length=150, blank=True, default='', help_text='e.g., Physics Teacher, 9A Student')
	about = models.TextField(blank=True, default='')
	contacts = models.JSONField(blank=True, null=True, help_text='{"phone":"+998...","email":"..."}')

	class Meta:
		verbose_name = 'Rolga xos profil (umumiy)'
		verbose_name_plural = 'Rolga xos profillar (umumiy)'

	def __str__(self):  # pragma: no cover - trivial
		return f"UserBranchProfile<{self.user_branch_id}>"


class TeacherProfile(BaseModel):
	"""Teacher-specific profile fields linked to a branch membership.

	We avoid multi-table inheritance for clarity and direct OneToOne composition.
	"""
	user_branch = models.OneToOneField('branch.BranchMembership', on_delete=models.CASCADE, related_name='teacher_profile')
	subject = models.CharField(max_length=120, blank=True, default='')
	experience_years = models.PositiveIntegerField(blank=True, null=True)
	bio = models.TextField(blank=True, default='')

	class Meta:
		verbose_name = 'O‘qituvchi profili'
		verbose_name_plural = 'O‘qituvchi profillari'

	def __str__(self):  # pragma: no cover - trivial
		return f"TeacherProfile<{self.user_branch_id}>"


class StudentProfile(BaseModel):
	"""Maktab o'quvchilari uchun to'liq profil.
	
	Maktab o'quvchilarining barcha ma'lumotlari shu modelda saqlanadi.
	"""
	user_branch = models.OneToOneField(
		'branch.BranchMembership',
		on_delete=models.CASCADE,
		related_name='student_profile',
		verbose_name='O\'quvchi a\'zoligi'
	)
	
	# Shaxsiy raqam (avtomatik generatsiya)
	personal_number = models.CharField(
		max_length=50,
		unique=True,
		db_index=True,
		blank=True,
		null=True,
		verbose_name='Shaxsiy raqam',
		help_text='O\'quvchining shaxsiy raqami (avtomatik generatsiya qilinadi)'
	)
	
	# Asosiy ma'lumotlar
	middle_name = models.CharField(
		max_length=150,
		blank=True,
		default='',
		verbose_name='Otasining ismi',
		help_text='O\'quvchining otasining ismi'
	)
	
	# Jinsi
	gender = models.CharField(
		max_length=16,
		choices=Gender.choices,
		default=Gender.UNSPECIFIED,
		verbose_name='Jinsi'
	)
	
	# Tu'gilgan sana
	date_of_birth = models.DateField(
		blank=True,
		null=True,
		verbose_name='Tu\'gilgan sana'
	)
	
	# Manzil
	address = models.TextField(
		blank=True,
		default='',
		verbose_name='Manzil',
		help_text='O\'quvchining to\'liq manzili'
	)
	
	# Tu'gilganlik guvohnoma rasmi
	birth_certificate = models.FileField(
		upload_to='students/birth_certificates/',
		blank=True,
		null=True,
		verbose_name='Tu\'gilganlik guvohnoma rasmi',
		help_text='Tu\'gilganlik guvohnoma rasmi (PDF yoki rasm)'
	)
	
	# Qo'shimcha ma'lumotlar (JSON formatida)
	additional_fields = models.JSONField(
		blank=True,
		null=True,
		default=dict,
		verbose_name='Qo\'shimcha ma\'lumotlar',
		help_text='Qo\'shimcha ma\'lumotlar JSON formatida. Masalan: {"passport_number": "AB1234567", "nationality": "UZ"}'
	)
	
	# Eski fieldlar (backward compatibility)
	grade = models.CharField(max_length=32, blank=True, default='', verbose_name='Sinf (eski)')
	enrollment_date = models.DateField(blank=True, null=True, verbose_name='Qabul qilingan sana')
	parent_name = models.CharField(max_length=150, blank=True, default='', verbose_name='Ota-ona ismi (eski)')

	class Meta:
		verbose_name = 'O\'quvchi profili'
		verbose_name_plural = 'O\'quvchi profillari'
		indexes = [
			models.Index(fields=['date_of_birth']),
			models.Index(fields=['gender']),
			models.Index(fields=['personal_number']),
		]

	def __str__(self):
		user = self.user_branch.user
		full_name = user.get_full_name()
		if self.middle_name:
			full_name = f"{user.first_name} {self.middle_name} {user.last_name}".strip()
		return f"StudentProfile<{full_name or user.phone_number}>"
	
	@property
	def full_name(self):
		"""O'quvchining to'liq ismi (ism, otasining ismi, familiya)."""
		user = self.user_branch.user
		if self.middle_name:
			return f"{user.first_name} {self.middle_name} {user.last_name}".strip()
		return user.get_full_name()
	
	@property
	def current_class(self):
		"""O'quvchining joriy sinfi."""
		from apps.school.classes.models import ClassStudent
		class_student = ClassStudent.objects.filter(
			membership=self.user_branch,
			deleted_at__isnull=True,
			is_active=True
		).select_related('class_obj').first()
		return class_student.class_obj if class_student else None
	
	def generate_personal_number(self):
		"""Shaxsiy raqam generatsiya qilish.
		
		Format: ST-YYYY-NNNN
		Masalan: ST-2024-0001
		"""
		from django.utils import timezone
		from django.db.models import Max
		
		year = timezone.now().year
		prefix = f"ST-{year}-"
		
		# Bu yilgi eng katta raqamni topish
		last_number = StudentProfile.objects.filter(
			personal_number__startswith=prefix,
			deleted_at__isnull=True
		).aggregate(
			max_num=Max('personal_number')
		)['max_num']
		
		if last_number:
			# Oxirgi raqamdan keyingi raqamni olish
			try:
				last_num = int(last_number.split('-')[-1])
				next_num = last_num + 1
			except (ValueError, IndexError):
				next_num = 1
		else:
			next_num = 1
		
		# 4 xonali formatda yozish
		personal_number = f"{prefix}{next_num:04d}"
		
		# Agar bu raqam allaqachon mavjud bo'lsa, keyingisini qidirish
		while StudentProfile.objects.filter(personal_number=personal_number).exists():
			next_num += 1
			personal_number = f"{prefix}{next_num:04d}"
		
		return personal_number
	
	def save(self, *args, **kwargs):
		"""Save metodida shaxsiy raqam generatsiya qilish."""
		if not self.personal_number:
			self.personal_number = self.generate_personal_number()
		super().save(*args, **kwargs)


class ParentProfile(BaseModel):
	"""Parent-specific profile fields linked to a branch membership."""
	user_branch = models.OneToOneField('branch.BranchMembership', on_delete=models.CASCADE, related_name='parent_profile')
	notes = models.TextField(blank=True, default='')
	related_students = models.ManyToManyField(StudentProfile, blank=True, related_name='parent_links')

	class Meta:
		verbose_name = 'Ota-ona profili'
		verbose_name_plural = 'Ota-ona profillari'

	def __str__(self):  # pragma: no cover - trivial
		return f"ParentProfile<{self.user_branch_id}>"


class AdminProfile(BaseModel):
		"""Admin-specific profile for branch_admin and super_admin memberships.

		Note on relation target:
		- We intentionally link to the legacy concrete model 'users.UserBranch' rather than the
			proxy 'apps.branch.BranchMembership'. Django does not allow ForeignKey/OneToOne to
			proxy models because they don't have their own table. Since BranchMembership is a
			proxy over the same table, using 'users.UserBranch' keeps backward compatibility and
			requires no schema changes, while still working transparently with the proxy in code.
		"""

		# Keep field name consistent with other role profiles for DX and admin inlines
		user_branch = models.OneToOneField('branch.BranchMembership', on_delete=models.CASCADE, related_name='admin_profile')

		# True when the membership role is super_admin; branch_admin remains False
		is_super_admin = models.BooleanField(default=False)

		# Optional: which branches this admin manages; useful for UI scoping/filters
		managed_branches = models.ManyToManyField('branch.Branch', blank=True, related_name='managed_by_admin_profiles')

		# Optional fields for display in UI
		title = models.CharField(max_length=255, blank=True, default='')
		notes = models.TextField(blank=True, default='')

		class Meta:
				verbose_name = 'Admin profili'
				verbose_name_plural = 'Admin profillari'

		def __str__(self):  # pragma: no cover - trivial
				return f"AdminProfile<{self.user_branch_id}, super={self.is_super_admin}>"


class RelativeType(models.TextChoices):
	"""Yaqinlar munosabat turlari."""
	FATHER = 'father', 'Otasi'
	MOTHER = 'mother', 'Onasi'
	BROTHER = 'brother', 'Akasi'
	SISTER = 'sister', 'Opasi'
	GRANDFATHER = 'grandfather', 'Bobosi'
	GRANDMOTHER = 'grandmother', 'Buvisi'
	UNCLE = 'uncle', 'Amakisi/Tog\'asi'
	AUNT = 'aunt', 'Xolasi/Tog\'asi'
	GUARDIAN = 'guardian', 'Vasiy'
	OTHER = 'other', 'Boshqa'


class StudentRelative(BaseModel):
	"""O'quvchi yaqinlari.
	
	O'quvchining yaqinlari (otasi, onasi, akasi va h.k.) ma'lumotlari.
	"""
	student_profile = models.ForeignKey(
		'profiles.StudentProfile',
		on_delete=models.CASCADE,
		related_name='relatives',
		verbose_name='O\'quvchi profili'
	)
	
	# Munosabat turi
	relationship_type = models.CharField(
		max_length=20,
		choices=RelativeType.choices,
		verbose_name='Munosabat turi'
	)
	
	# Ism va familiya
	first_name = models.CharField(
		max_length=150,
		verbose_name='Ism'
	)
	last_name = models.CharField(
		max_length=150,
		blank=True,
		default='',
		verbose_name='Familiya'
	)
	middle_name = models.CharField(
		max_length=150,
		blank=True,
		default='',
		verbose_name='Otasining ismi'
	)
	
	# Telefon raqami
	phone_number = models.CharField(
		max_length=20,
		blank=True,
		default='',
		validators=[RegexValidator(r"^\+?[0-9]{7,15}$", "Telefon raqami noto'g'ri formatda")],
		verbose_name='Telefon raqami'
	)
	
	# Email
	email = models.EmailField(
		blank=True,
		null=True,
		verbose_name='Email',
		help_text='Email manzili'
	)
	
	# Jinsi
	gender = models.CharField(
		max_length=16,
		choices=Gender.choices,
		default=Gender.UNSPECIFIED,
		verbose_name='Jinsi'
	)
	
	# Tu'gilgan sana
	date_of_birth = models.DateField(
		blank=True,
		null=True,
		verbose_name='Tu\'gilgan sana'
	)
	
	# Manzil
	address = models.TextField(
		blank=True,
		default='',
		verbose_name='Manzil',
		help_text='To\'liq manzil'
	)
	
	# Ish joyi
	workplace = models.CharField(
		max_length=255,
		blank=True,
		default='',
		verbose_name='Ish joyi',
		help_text='Ish joyi nomi'
	)
	
	# Lavozim
	position = models.CharField(
		max_length=255,
		blank=True,
		default='',
		verbose_name='Lavozim',
		help_text='Ish lavozimi'
	)
	
	# Pasport ma'lumotlari
	passport_number = models.CharField(
		max_length=50,
		blank=True,
		default='',
		verbose_name='Pasport raqami',
		help_text='Pasport yoki ID karta raqami'
	)
	
	# Rasmi
	photo = models.ImageField(
		upload_to='students/relatives/',
		blank=True,
		null=True,
		verbose_name='Rasm',
		help_text='Yaqinning rasmi'
	)
	
	# Asosiy kontakt
	is_primary_contact = models.BooleanField(
		default=False,
		verbose_name='Asosiy kontakt',
		help_text='Bu yaqin asosiy kontakt bo\'lsa'
	)
	
	# Vasiy
	is_guardian = models.BooleanField(
		default=False,
		verbose_name='Vasiy',
		help_text='Bu yaqin vasiy bo\'lsa'
	)
	
	# Qo'shimcha ma'lumotlar
	additional_info = models.JSONField(
		blank=True,
		null=True,
		default=dict,
		verbose_name='Qo\'shimcha ma\'lumotlar',
		help_text='Qo\'shimcha ma\'lumotlar JSON formatida. Masalan: {"education": "...", "income": "..."}'
	)
	
	# Izohlar
	notes = models.TextField(
		blank=True,
		default='',
		verbose_name='Izohlar'
	)

	class Meta:
		verbose_name = 'O\'quvchi yaqini'
		verbose_name_plural = 'O\'quvchi yaqinlari'
		indexes = [
			models.Index(fields=['student_profile', 'relationship_type']),
			models.Index(fields=['phone_number']),
			models.Index(fields=['is_primary_contact']),
			models.Index(fields=['is_guardian']),
		]
		ordering = ['relationship_type', 'first_name']

	def __str__(self):
		full_name = f"{self.first_name} {self.middle_name} {self.last_name}".strip() if self.middle_name else f"{self.first_name} {self.last_name}".strip()
		return f"{self.get_relationship_type_display()} - {full_name}"
	
	@property
	def full_name(self):
		"""Yaqinning to'liq ismi."""
		if self.middle_name:
			return f"{self.first_name} {self.middle_name} {self.last_name}".strip()
		return f"{self.first_name} {self.last_name}".strip()
