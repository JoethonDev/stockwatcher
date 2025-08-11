from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Exists, OuterRef
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .models import Alert, TriggeredAlert, Company
from .serializers import (
    CompanySerializer,
    AlertCreateSerializer,
    AlertListSerializer,
    TriggeredAlertSerializer
)
from .scheduler import create_or_enable_user_task, disable_user_task_if_needed


@extend_schema(
    summary="List all available companies",
    description="Provides a cached, public list of all companies whose stocks can be tracked.",
    responses={
        200: OpenApiResponse(response=CompanySerializer(many=True), description="List of companies")
    }
)
@method_decorator(cache_page(settings.CACHE_PAGE_DURATION), name='dispatch')
class CompanyListView(generics.ListAPIView):
    queryset = Company.objects.all().order_by('stock_symbol')
    serializer_class = CompanySerializer
    permission_classes = [AllowAny]


@extend_schema(
    summary="List and create alerts",
    description="GET: List all alerts for the authenticated user. POST: Create a new alert.",
    parameters=[
        OpenApiParameter(name='is_active', description='Filter by active status (true/false)', required=False, type=str),
        OpenApiParameter(name='triggered', description='Filter by triggered status (true/false)', required=False, type=str),
    ],
    responses={
        200: OpenApiResponse(response=AlertListSerializer(many=True), description="List of alerts"),
        201: OpenApiResponse(response=AlertListSerializer, description="Alert created"),
        400: OpenApiResponse(description="Bad request - invalid input"),
        401: OpenApiResponse(description="Unauthorized - login required"),
    },
    request=AlertCreateSerializer
)
class AlertListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AlertCreateSerializer
        return AlertListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Alert.objects.filter(user=user).select_related('company')

        is_active_param = self.request.query_params.get('is_active')
        if is_active_param is not None:
            queryset = queryset.filter(is_active=(is_active_param.lower() == 'true'))

        triggered_param = self.request.query_params.get('triggered')
        if triggered_param is not None:
            subquery = TriggeredAlert.objects.filter(alert=OuterRef('pk'))
            queryset = queryset.annotate(has_triggered=Exists(subquery))
            queryset = queryset.filter(has_triggered=(triggered_param.lower() == 'true'))

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        alert = serializer.save(user=self.request.user)
        create_or_enable_user_task(alert.user)


@extend_schema(
    summary="Retrieve or delete an alert",
    description="GET: Retrieve a specific alert by ID. DELETE: Delete an alert and remove associated tasks.",
    responses={
        200: OpenApiResponse(response=AlertListSerializer, description="Alert detail"),
        204: OpenApiResponse(description="Alert deleted"),
        404: OpenApiResponse(description="Alert not found or access denied")
    }
)
class AlertDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertListSerializer

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        disable_user_task_if_needed(user)


@extend_schema(
    summary="Reactivate a disabled alert",
    description="Reactivates a previously triggered and disabled alert. Resets monitoring conditions.",
    request=None,
    responses={
        200: OpenApiResponse(response=AlertListSerializer, description="Alert reactivated"),
        404: OpenApiResponse(description="Alert not found or access denied")
    }
)
class AlertReactivateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AlertListSerializer
    http_method_names = ['patch']

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(is_active=True, condition_met_since=None)
        create_or_enable_user_task(self.request.user)

@extend_schema(
    summary="List triggered alerts",
    description="Returns a paginated history of triggered alerts for the authenticated user.",
    responses={
        200: OpenApiResponse(response=TriggeredAlertSerializer(many=True), description="Triggered alert history"),
        401: OpenApiResponse(description="Unauthorized - login required")
    }
)
class TriggeredAlertListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TriggeredAlertSerializer

    def get_queryset(self):
        return TriggeredAlert.objects.filter(user=self.request.user).order_by('-timestamp')
