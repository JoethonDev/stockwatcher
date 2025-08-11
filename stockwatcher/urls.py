from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', lambda request: redirect('swagger-ui', permanent=False)),

    # Django Admin
    path('admin/', admin.site.urls),

    # API Schema and Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # API Endpoints
    path('api/users/', include("users.urls")),
    path('api/alerts/', include("alerts.urls")),
]