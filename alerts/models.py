from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Company(models.Model):
    stock_symbol = models.CharField(max_length=10, unique=True, null=False)
    current_price = models.FloatField(default=0, null=False)

    def __str__(self):
        return f'{self.stock_symbol}'

class Alert(models.Model):
    class AlertType(models.TextChoices):
        PRICE_THRESHOLD = 'PRICE_THRESHOLD', 'Price Threshold'
        PRICE_DURATION = 'PRICE_DURATION', 'Price Duration'

    class TriggerCondition(models.TextChoices):
        GREATER_THAN = 'GT', 'Greater Than'
        LESS_THAN = 'LT', 'Less Than'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts', db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='setted_alerts')
    threshold = models.FloatField(default=0, help_text="The price that triggers the alert.")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Required only for duration-based alerts.")
    alert_type = models.CharField(max_length=20, choices=AlertType.choices, default=AlertType.PRICE_THRESHOLD)
    condition = models.CharField(max_length=20, choices=TriggerCondition.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    condition_met_since = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Internal timestamp for tracking when a duration condition started being met."
    )

    def __str__(self):
        return f'Alert for {self.company.stock_symbol} ({self.get_condition_display()} {self.threshold})'

    def is_condition_met(self, current_price: float) -> bool:
        """
        Checks if the alert's price condition is met given the current price.

        Args:
            current_price (float): The current market price of the stock.

        Returns:
            bool: True if the condition is met, False otherwise.
        """
        if self.condition == self.TriggerCondition.GREATER_THAN:
            return current_price > self.threshold
        if self.condition == self.TriggerCondition.LESS_THAN:
            return current_price < self.threshold
        return False

    def has_duration_met(self, current_timestamp: timezone) -> bool:
        """
        Checks if the required duration has passed since the condition was first met.
        This method does NOT change the state of the object.

        Args:
            current_timestamp (datetime): The current time to check against.

        Returns:
            bool: True if the duration has been met, False otherwise.
        """
        if self.alert_type != self.AlertType.PRICE_DURATION:
            return True
        if self.condition_met_since is None:
            return False
        required_duration = timedelta(minutes=self.duration_minutes)
        return current_timestamp >= (self.condition_met_since + required_duration)

class TriggeredAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='triggered_alerts')
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='triggers')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Triggered: {self.alert} at {self.timestamp.strftime("%Y-%m-%d %H:%M")}'
