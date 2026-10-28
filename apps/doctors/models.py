from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.patients.models import phone_validator


class Doctor(models.Model):
    name = models.CharField(max_length=255)
    specialization = models.CharField(max_length=150, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    experience_years = models.IntegerField(
        validators=[MinValueValidator(0, message="Experience years cannot be negative.")]
    )
    hospital = models.CharField(max_length=255, default="Synora Central Clinic")
    is_available = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctors'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['specialization']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"Dr. {self.name} - {self.specialization}"
