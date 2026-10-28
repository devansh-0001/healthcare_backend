from rest_framework import viewsets, permissions
from apps.patients.models import Patient
from apps.patients.serializers import PatientSerializer


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Patient management.
    Scoped strictly to the authenticated user's own patients.
    Attempting to access, edit, or delete another user's patient returns 404.
    """
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Patient.objects.none()
        return Patient.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
