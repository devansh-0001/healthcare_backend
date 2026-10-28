from django.db import models
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class PatientDoctorMapping(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='doctor_mappings',
        db_index=True
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='patient_mappings'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_at']
        unique_together = ('patient', 'doctor')
        indexes = [
            models.Index(fields=['patient']),
        ]

    def __str__(self):
        return f"Patient: {self.patient.name} -> Doctor: {self.doctor.name}"
