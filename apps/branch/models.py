from django.db import models
from django.core.validators import RegexValidator
from apps.common.models import BaseModel, BaseManager
from auth.users.models import UserBranch
from django.utils.text import slugify


class BranchTypes(models.TextChoices):
    SCHOOL = 'school', 'Maktab'
    CENTER = 'center', 'Markaz'

class BranchStatuses(models.TextChoices):
    PENDING = 'pending', 'Kutilmoqda'
    ACTIVE = 'active', 'Faol'
    INACTIVE = 'inactive', 'Nofaol'
    ARCHIVED = 'archived', 'Arxivlangan'


class BranchQuerySet(models.QuerySet):
    """Extra helpers for filtering branches by type and status"""

    # Type filters
    def schools(self):
        return self.filter(type=BranchTypes.SCHOOL)

    def centers(self):
        return self.filter(type=BranchTypes.CENTER)

    # Status filters (note: not to be confused with BaseModel.active which means not soft-deleted)
    def status_pending(self):
        return self.filter(status=BranchStatuses.PENDING)

    def status_active(self):
        return self.filter(status=BranchStatuses.ACTIVE)

    def status_inactive(self):
        return self.filter(status=BranchStatuses.INACTIVE)

    def status_archived(self):
        return self.filter(status=BranchStatuses.ARCHIVED)


class BranchManager(BaseManager.from_queryset(BranchQuerySet)):
    """Manager that combines soft-delete helpers and branch-specific filters"""
    pass

class Branch(BaseModel):
    name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Nomi',
        help_text='Filial nomi'
    )
    type = models.CharField(
        max_length=20,
        choices=BranchTypes.choices,
        default=BranchTypes.SCHOOL,
        verbose_name='Turi'
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name='Slug',
        help_text='Filial uchun unikal nom (slug)'
    )

    status = models.CharField(
        max_length=20,
        choices=BranchStatuses.choices,
        default=BranchStatuses.PENDING,
        verbose_name='Holati'
    )

    address = models.TextField(blank=True, null=True, verbose_name='Manzil')
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?[0-9]{7,15}$', 'Telefon raqami noto\'g\'ri formatda')],
        verbose_name='Telefon raqami'
    )
    email = models.EmailField(blank=True, null=True, verbose_name='Email')

    # Attach combined manager
    objects = BranchManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiallar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['name', 'type']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BranchMembership(UserBranch):
    """Canonical proxy for membership; use this import moving forward.

    Remains a proxy to avoid schema and relation changes; all reverse relations
    and signals continue to work via the underlying UserBranch model.
    """

    class Meta:
        proxy = True
        verbose_name = "Branch membership"
        verbose_name_plural = "Branch memberships"