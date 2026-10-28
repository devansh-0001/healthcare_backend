from rest_framework import serializers
from rest_framework.exceptions import NotFound
from apps.mappings.models import PatientDoctorMapping
from apps.patients.models import Patient
from apps.doctors.models import Doctor
from apps.doctors.serializers import DoctorSerializer


class PatientDoctorMappingCreateSerializer(serializers.ModelSerializer):
    patient = serializers.IntegerField(write_only=True)
    doctor = serializers.IntegerField(write_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ('id', 'patient', 'doctor', 'assigned_at')
        read_only_fields = ('id', 'assigned_at')

    def validate_patient(self, value):
        request = self.context.get('request')
        try:
            patient = Patient.objects.get(id=value, created_by=request.user)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found.")
        return patient

    def validate_doctor(self, value):
        try:
            doctor = Doctor.objects.get(id=value)
        except Doctor.DoesNotExist:
            raise NotFound("Doctor not found.")
        return doctor

    def validate(self, attrs):
        patient = attrs['patient']
        doctor = attrs['doctor']

        if PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
            raise serializers.ValidationError(
                {"doctor": ["This doctor is already assigned to this patient."]}
            )
        return attrs

    def create(self, validated_data):
        return PatientDoctorMapping.objects.create(
            patient=validated_data['patient'],
            doctor=validated_data['doctor']
        )


class PatientDoctorMappingDetailSerializer(serializers.ModelSerializer):
    patient_id = serializers.ReadOnlyField(source='patient.id')
    patient_name = serializers.ReadOnlyField(source='patient.name')
    doctor_id = serializers.ReadOnlyField(source='doctor.id')
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = (
            'id',
            'patient_id',
            'patient_name',
            'doctor_id',
            'doctor',
            'assigned_at'
        )
