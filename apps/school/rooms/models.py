from django.db import models
from django.db.models import Q
from django.conf import settings
from apps.common.models import BaseModel
from apps.branch.models import Branch


class RoomType(models.TextChoices):
    """Xona turlari."""
    CLASSROOM = 'classroom', 'Dars xonasi'
    LAB = 'lab', 'Laboratoriya'
    LIBRARY = 'library', 'Kutubxona'
    GYM = 'gym', 'Sport zali'
    OFFICE = 'office', 'Ofis'
    AUDITORIUM = 'auditorium', 'Auditoriya'
    OTHER = 'other', 'Boshqa'


class Building(BaseModel):
    """Bino modeli.
    
    Har bir filial uchun binolar yaratiladi.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='buildings',
        verbose_name='Filial'
    )
    name = models.CharField(
        max_length=255,
        verbose_name='Bino nomi',
        help_text='Masalan: "Asosiy bino", "Yangi bino"'
    )
    address = models.TextField(
        blank=True,
        default='',
        verbose_name='Manzil',
        help_text='Bino manzili'
    )
    floors = models.IntegerField(
        default=1,
        verbose_name='Qavatlar soni',
        help_text='Binodagi qavatlar soni'
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Tavsif',
        help_text='Bino haqida qo\'shimcha ma\'lumot'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol bino',
        help_text='Bu bino faolmi?'
    )
    
    class Meta:
        verbose_name = 'Bino'
        verbose_name_plural = 'Binolar'
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'name'],
                condition=Q(deleted_at__isnull=True),
                name='uniq_building_branch_name_active'
            ),
        ]
        indexes = [
            models.Index(fields=['branch', 'is_active']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} @ {self.branch.name}"

    def delete(self, using=None, keep_parents=False, hard=False):
        """Soft-delete paytida binoni nofaol qilib qo'yish."""
        if not hard and self.is_active:
            type(self).objects.filter(pk=self.pk).update(is_active=False)
            self.is_active = False
        return super().delete(using=using, keep_parents=keep_parents, hard=hard)

    def restore(self):
        super().restore()
        if not self.is_active:
            self.is_active = True
            self.save(update_fields=['is_active'])
        return self


class Room(BaseModel):
    """Xona modeli.
    
    Har bir bino uchun xonalar yaratiladi.
    """
    
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='Filial'
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name='Bino'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Xona nomi',
        help_text='Masalan: "101", "Laboratoriya"'
    )
    room_type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.CLASSROOM,
        verbose_name='Xona turi'
    )
    floor = models.IntegerField(
        default=1,
        verbose_name='Qavat',
        help_text='Xona qaysi qavatda joylashgan'
    )
    capacity = models.IntegerField(
        default=30,
        verbose_name='Sig\'imi',
        help_text='Xonada necha kishi sig\'adi (o\'quvchilar soni)'
    )
    equipment = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Jihozlar',
        help_text='Jihozlar ro\'yxati: [{"name": "projector", "quantity": 1, "unit": "pcs"}]'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Faol xona',
        help_text='Bu xona faolmi?'
    )
    
    class Meta:
        verbose_name = 'Xona'
        verbose_name_plural = 'Xonalar'
        constraints = [
            models.UniqueConstraint(
                fields=['branch', 'building', 'name'],
                condition=Q(deleted_at__isnull=True),
                name='uniq_room_branch_building_name_active'
            ),
        ]
        indexes = [
            models.Index(fields=['branch', 'is_active']),
            models.Index(fields=['building', 'is_active']),
            models.Index(fields=['room_type']),
            models.Index(fields=['floor']),
        ]
        ordering = ['building', 'floor', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.building.name}) @ {self.branch.name}"
    
    def save(self, *args, **kwargs):
        """Validate that building belongs to the same branch."""
        if self.building.branch != self.branch:
            raise ValueError("Building must belong to the same branch as the room")
        
        # Validate floor is within building floors
        if self.floor > self.building.floors:
            raise ValueError(f"Floor cannot be greater than building floors ({self.building.floors})")
        
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, hard=False):
        """Soft-delete paytida xonani nofaol qilish."""
        if not hard and self.is_active:
            type(self).objects.filter(pk=self.pk).update(is_active=False)
            self.is_active = False
        return super().delete(using=using, keep_parents=keep_parents, hard=hard)

    def restore(self):
        super().restore()
        if not self.is_active:
            self.is_active = True
            self.save(update_fields=['is_active'])
        return self

