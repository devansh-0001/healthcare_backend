from django.contrib import admin
from django.urls import path, include
from common.views import StatsView, IndexView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='synora-home'),
    path('api/auth/', include('apps.users.urls')),
    path('api/patients/', include('apps.patients.urls')),
    path('api/doctors/', include('apps.doctors.urls')),
    path('api/mappings/', include('apps.mappings.urls')),
    path('api/stats/', StatsView.as_view(), name='api-stats'),
]
