from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator

phone_validator = RegexValidator(
    regex=r'^\+?[0-9]{10,15}$',
    message="Phone number must contain between 10 and 15 digits, optionally prefixed with '+'."
)


class Patient(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    name = models.CharField(max_length=255)
    age = models.IntegerField(
        validators=[
            MinValueValidator(0, message="Age must be at least 0."),
            MaxValueValidator(120, message="Age cannot exceed 120.")
        ]
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20, validators=[phone_validator])
    address = models.TextField()
    medical_history = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patients',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.age}, {self.gender})"
