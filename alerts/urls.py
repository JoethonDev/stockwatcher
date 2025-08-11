from django.urls import path
from .views import (
    CompanyListView,
    AlertListCreateView,
    AlertDetailView,
    AlertReactivateView,
    TriggeredAlertListView
)

urlpatterns = [
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('', AlertListCreateView.as_view(), name='alert-list-create'),
    path('<int:pk>/', AlertDetailView.as_view(), name='alert-detail'),
    path('<int:pk>/reactivate/', AlertReactivateView.as_view(), name='alert-reactivate'),
    path('triggered/', TriggeredAlertListView.as_view(), name='triggered-alert-list'),
]