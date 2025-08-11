from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import Alert, TriggeredAlert, Company

@extend_schema_serializer(
    exclude_fields=[],
    examples=[
        OpenApiExample(
            'Company Example',
            value={
                "id": 1,
                "stock_symbol": "AAPL",
                "current_price": 198.12
            },
            response_only=True
        )
    ]
)
class CompanySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the Company model.
    Includes stock symbol and the current price.
    """

    class Meta:
        model = Company
        fields = ['id', 'stock_symbol', 'current_price']

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Create Alert Example',
            value={
                "company": 1,
                "threshold": 250.5,
                "duration_minutes": 30,
                "alert_type": "PRICE_DURATION",
                "condition": "GREATER_THAN"
            },
            request_only=True
        )
    ]
)
class AlertCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new alert.
    """

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        help_text="ID of the company this alert is for."
    )

    class Meta:
        model = Alert
        fields = [
            'company',
            'threshold',
            'duration_minutes',
            'alert_type',
            'condition'
        ]

    def validate(self, data):
        alert_type = data.get('alert_type')
        duration = data.get('duration_minutes')

        if alert_type == Alert.AlertType.PRICE_DURATION and not duration:
            raise serializers.ValidationError({
                'duration_minutes': 'This field is required for duration-based alerts.'
            })

        if alert_type == Alert.AlertType.PRICE_THRESHOLD and duration is not None:
            data['duration_minutes'] = None

        return data

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Alert List Example',
            value={
                "id": 5,
                "company": {
                    "id": 1,
                    "stock_symbol": "AAPL",
                    "current_price": 198.12
                },
                "alert_type": "PRICE_THRESHOLD",
                "condition": "GREATER_THAN",
                "threshold": 200.0,
                "duration_minutes": None,
                "is_active": True,
                "has_triggered": False,
                "created_at": "2025-08-10T14:00:00Z"
            },
            response_only=True
        )
    ]
)
class AlertListSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for listing alerts.
    """
    company = CompanySerializer(read_only=True)
    has_triggered = serializers.SerializerMethodField(
        help_text="True if this alert has ever been triggered."
    )

    class Meta:
        model = Alert
        fields = [
            'id',
            'company',
            'alert_type',
            'condition',
            'threshold',
            'duration_minutes',
            'is_active',
            'has_triggered',
            'created_at'
        ]

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_has_triggered(self, obj: Alert) -> bool:
        return obj.triggers.exists()

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Triggered Alert Example',
            value={
                "id": 12,
                "alert": {
                    "id": 5,
                    "company": {
                        "id": 1,
                        "stock_symbol": "AAPL",
                        "current_price": 198.12
                    },
                    "alert_type": "PRICE_THRESHOLD",
                    "condition": "GREATER_THAN",
                    "threshold": 200.0,
                    "duration_minutes": None,
                    "is_active": True,
                    "has_triggered": True,
                    "created_at": "2025-08-10T14:00:00Z"
                },
                "timestamp": "2025-08-10T14:50:00Z"
            },
            response_only=True
        )
    ]
)
class TriggeredAlertSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for triggered alerts (alert history).
    """
    alert = AlertListSerializer(read_only=True)

    class Meta:
        model = TriggeredAlert
        fields = ['id', 'alert', 'timestamp']
