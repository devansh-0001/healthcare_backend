from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from apps.doctors.models import Doctor
from apps.doctors.serializers import DoctorSerializer
from common.permissions import IsCreatorOrReadOnly


class DoctorFilter(django_filters.FilterSet):
    specialization = django_filters.CharFilter(field_name='specialization', lookup_expr='iexact')
    is_available = django_filters.BooleanFilter(field_name='is_available')

    class Meta:
        model = Doctor
        fields = ['specialization', 'is_available']


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Doctor management.
    All authenticated users can list and retrieve doctors.
    Only the creator can update or delete a doctor record.
    """
    queryset = Doctor.objects.select_related('created_by').all()
    serializer_class = DoctorSerializer
    permission_classes = [IsCreatorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DoctorFilter
    search_fields = ['name', 'specialization', 'hospital']
    ordering_fields = ['name', 'experience_years', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
