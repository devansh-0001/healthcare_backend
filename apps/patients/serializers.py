from rest_framework import serializers
from apps.patients.models import Patient, phone_validator


class PatientSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(validators=[phone_validator])

    class Meta:
        model = Patient
        fields = (
            'id',
            'name',
            'age',
            'gender',
            'phone',
            'address',
            'medical_history',
            'created_at',
            'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Patient name cannot be empty.")
        return value.strip()

    def validate_age(self, value):
        if value < 0 or value > 120:
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return value

    def validate_gender(self, value):
        value_lower = value.strip().lower()
        valid_genders = dict(Patient.GENDER_CHOICES).keys()
        if value_lower not in valid_genders:
            raise serializers.ValidationError(
                f"Gender must be one of: {', '.join(valid_genders)}."
            )
        return value_lower

    def validate_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Address is required.")
        return value.strip()
