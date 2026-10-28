from django.urls import path
from apps.mappings.views import MappingListCreateView, MappingDetailPatientView

urlpatterns = [
    path('', MappingListCreateView.as_view(), name='mapping-list-create'),
    path('<int:pk>/', MappingDetailPatientView.as_view(), name='mapping-detail-or-delete'),
]
