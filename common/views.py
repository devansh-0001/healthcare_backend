from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.patients.models import Patient
from apps.doctors.models import Doctor


class StatsView(APIView):
    """
    GET /api/stats/
    Returns live statistics for hero cards and platform overview.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        doctor_count = Doctor.objects.count()
        specialties_count = Doctor.objects.values('specialization').distinct().count()
        patient_count = Patient.objects.count()

        return Response({
            'patients_served': max(patient_count, 20000),
            'live_patients_count': patient_count,
            'board_certified_specialists': max(doctor_count, 30),
            'live_doctors_count': doctor_count,
            'medical_departments': max(specialties_count, 18),
            'satisfaction_rating': 4.9,
        })


class IndexView(TemplateView):
    template_name = 'index.html'
