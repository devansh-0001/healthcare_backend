from rest_framework import serializers
from apps.doctors.models import Doctor
from apps.patients.models import phone_validator
from common.exceptions import ConflictError


class DoctorSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[phone_validator])
    created_by_name = serializers.ReadOnlyField(source='created_by.name')

    class Meta:
        model = Doctor
        fields = (
            'id',
            'name',
            'specialization',
            'email',
            'phone',
            'experience_years',
            'hospital',
            'is_available',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_by', 'created_by_name', 'created_at', 'updated_at')
        extra_kwargs = {
            'email': {
                'validators': []
            }
        }

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Doctor name cannot be empty.")
        return value.strip()

    def validate_specialization(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Specialization is required.")
        return value.strip()

    def validate_email(self, value):
        normalized = value.strip().lower()
        query = Doctor.objects.filter(email__iexact=normalized)
        if self.instance:
            query = query.exclude(id=self.instance.id)
        if query.exists():
            raise ConflictError("A doctor with this email already exists.")
        return normalized

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError("Experience years cannot be negative.")
        return value
