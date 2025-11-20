from django.db import models
from django.contrib.auth.models import (
	AbstractBaseUser,
	BaseUserManager,
	PermissionsMixin,
)
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
from django.conf import settings
from apps.common.models import BaseModel


class UserManager(BaseUserManager):
	"""Custom user manager with phone_number as the unique identifier."""

	use_in_migrations = True

	def _create_user(self, phone_number: str, password: str | None, **extra_fields):
		if not phone_number:
			raise ValueError("The phone_number must be set")
		# Normalize: remove spaces and ensure leading + optional
		normalized = str(phone_number).strip().replace(" ", "")
		user = self.model(phone_number=normalized, **extra_fields)
		if password:
			user.set_password(password)
		else:
			# Set unusable password for OTP-only users
			user.set_unusable_password()
		user.save(using=self._db)
		return user

	def create_user(self, phone_number: str, password: str | None = None, **extra_fields):
		extra_fields.setdefault("is_staff", False)
		extra_fields.setdefault("is_superuser", False)
		extra_fields.setdefault("is_active", True)
		return self._create_user(phone_number, password, **extra_fields)

	def create_superuser(self, phone_number: str, password: str | None = None, **extra_fields):
		extra_fields.setdefault("is_staff", True)
		extra_fields.setdefault("is_superuser", True)
		extra_fields.setdefault("is_active", True)

		if extra_fields.get("is_staff") is not True:
			raise ValueError("Superuser must have is_staff=True.")
		if extra_fields.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True.")

		return self._create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	"""
	Custom User model using UUID primary key and phone_number as USERNAME_FIELD.
	Note: We keep boolean is_active separate from any soft-delete notion for compatibility with Django auth.
	"""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	phone_number = models.CharField(
		max_length=20,
		unique=True,
		db_index=True,
		validators=[RegexValidator(r"^\+?[0-9]{7,15}$", "Telefon raqami noto'g'ri formatda")],
		verbose_name="Telefon raqami",
	)
	first_name = models.CharField(max_length=150, blank=True, default="", verbose_name="Ism")
	last_name = models.CharField(max_length=150, blank=True, default="", verbose_name="Familiya")
	email = models.EmailField(blank=True, null=True)

	# Django auth flags
	is_staff = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	phone_verified = models.BooleanField(default=False, help_text="Telefon raqami tasdiqlanganmi")

	# Timestamps
	date_joined = models.DateTimeField(default=timezone.now)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	# Branch memberships (through model captures role)
	branches = models.ManyToManyField(
		'branch.Branch',
		through='branch.BranchMembership',
		through_fields=('user', 'branch'),
		related_name='users',
		blank=True
	)

	objects = UserManager()

	USERNAME_FIELD = "phone_number"
	REQUIRED_FIELDS: list[str] = []

	class Meta:
		verbose_name = "Foydalanuvchi"
		verbose_name_plural = "Foydalanuvchilar"
		ordering = ["-created_at"]

	def __str__(self) -> str:  # pragma: no cover - trivial
		return self.phone_number

	# Convenience alias matching business language
	@property
	def is_superadmin(self) -> bool:
		return bool(self.is_superuser)

	@property
	def auth_state(self) -> str:
		"""Return high-level auth state for frontend flow control."""
		if not self.phone_verified:
			return "NOT_VERIFIED"
		if not self.has_usable_password():
			return "NEEDS_PASSWORD"
		return "READY"


# BranchRole moved to apps.branch.models.BranchRole
# UserBranch removed - use apps.branch.models.BranchMembership instead

