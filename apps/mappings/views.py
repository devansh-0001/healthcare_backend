from django.db import transaction
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from apps.mappings.models import PatientDoctorMapping
from apps.patients.models import Patient
from apps.mappings.serializers import (
    PatientDoctorMappingCreateSerializer,
    PatientDoctorMappingDetailSerializer
)
from common.pagination import StandardResultsSetPagination


class MappingListCreateView(APIView):
    """
    POST /api/mappings/ - Assign doctor to patient.
    GET /api/mappings/ - List mappings for the requesting user's patients.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = PatientDoctorMapping.objects.filter(
            patient__created_by=request.user
        ).select_related('patient', 'doctor')

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PatientDoctorMappingDetailSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PatientDoctorMappingCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            mapping = serializer.save()
        detail_serializer = PatientDoctorMappingDetailSerializer(mapping)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)


class MappingDetailPatientView(APIView):
    """
    Handles:
    - GET /api/mappings/{patient_id}/ : Retrieve all doctors assigned to that patient.
    - DELETE /api/mappings/{id}/ : Remove the mapping assignment by mapping ID.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """
        pk is patient_id.
        Returns all doctors assigned to this patient.
        If patient doesn't exist or is not owned by requesting user -> 404.
        """
        try:
            patient = Patient.objects.get(id=pk, created_by=request.user)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found or you do not have permission to view it.")

        mappings = PatientDoctorMapping.objects.filter(
            patient=patient
        ).select_related('patient', 'doctor')

        serializer = PatientDoctorMappingDetailSerializer(mappings, many=True)
        return Response({
            'patient_id': patient.id,
            'patient_name': patient.name,
            'count': mappings.count(),
            'assigned_doctors': serializer.data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        pk is mapping id.
        Removes the assignment.
        Ensures the mapping belongs to a patient owned by requesting user -> 404 if not found.
        """
        try:
            mapping = PatientDoctorMapping.objects.select_related('patient').get(
                id=pk,
                patient__created_by=request.user
            )
        except PatientDoctorMapping.DoesNotExist:
            raise NotFound("Mapping not found or you do not have permission to remove it.")

        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
