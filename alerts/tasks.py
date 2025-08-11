import logging
import requests
import smtplib
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from celery import shared_task

from alerts.scheduler import disable_user_task_if_needed
from .models import Company, Alert, TriggeredAlert

# Get an instance of a logger for structured logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_stock_prices(self):
    """
    Celery task to fetch the latest prices for all companies from an external API
    and update the database. Runs on a global schedule.
    """
    logger.info("Starting task: update_stock_prices")
    try:
        BASE_URL = "https://financialmodelingprep.com/api/v3/quote/"
        API_KEY = settings.FMP_API_KEY
        if not API_KEY:
            logger.error("API_KEY for financialmodelingprep.com is not set.")
            return

        companies = list(Company.objects.all())
        if not companies:
            logger.info("No companies in the database to update.")
            return

        stock_symbols = [company.stock_symbol for company in companies]
        stock_path_params = ",".join(stock_symbols)
        
        api_url = f"{BASE_URL}{stock_path_params}"
        response = requests.get(api_url, params={"apikey": API_KEY}, timeout=30)
        response.raise_for_status()
        
        price_data = response.json()
        companies_map = {item['symbol']: item['price'] for item in price_data}

        updated_count = 0
        for company in companies:
            new_price = companies_map.get(company.stock_symbol)
            if new_price is not None:
                company.current_price = new_price
                updated_count += 1
        
        Company.objects.bulk_update(companies, ["current_price"])
        logger.info(f"Successfully updated prices for {updated_count} companies.")

    except requests.exceptions.RequestException as exc:
        logger.error(f"Network error updating stock prices: {exc}")
        raise self.retry(exc=exc)
    except (KeyError, TypeError) as exc:
        logger.error(f"Error parsing API response: {exc}")
    except Exception as exc:
        logger.error(f"An unexpected error in update_stock_prices: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def check_user_alerts(self, user_id):
    """
    Celery task to check all active alerts for a single user, using the
    user-provided logic. This task is scheduled dynamically on a per-user basis.
    """
    logger.info(f"Starting task: check_user_alerts for user_id: {user_id}")
    try:
        is_remaining_alerts = False
        triggered_alerts_to_create = []
        alerts_to_update = []
        now = timezone.now()
        
        user = User.objects.get(pk=user_id)
        alerts = list(Alert.objects.filter(user=user, is_active=True))
        
        if not alerts:
            logger.info(f"No active alerts found for user: {user.username}")
            return

        logger.info(f"Checking {len(alerts)} active alerts for user: {user.username}")

        for alert in alerts:
            condition_is_met = alert.is_condition_met()
            duration_is_met = alert.has_duration_met(now)

            if condition_is_met:
                if not duration_is_met:
                    is_remaining_alerts = True
                    alert.condition_met_since = alert.condition_met_since if alert.condition_met_since else now
                    alerts_to_update.append(alert)
                    continue

                alert.is_active = False
                alert.condition_met_since = None 
                triggered_alerts_to_create.append(
                    TriggeredAlert(user=user, alert=alert)
                )
                alerts_to_update.append(alert)
                continue
            
            if alert.alert_type == Alert.AlertType.PRICE_DURATION:
                alert.condition_met_since = None
                alerts_to_update.append(alert)
            is_remaining_alerts = True


        if triggered_alerts_to_create:
            created_triggered = TriggeredAlert.objects.bulk_create(triggered_alerts_to_create)
            logger.info(f"Created {len(created_triggered)} triggered alerts for user: {user.username}")
            send_email_notification.delay(user.id, [triggered.pk for triggered in created_triggered])

        if alerts_to_update:
            Alert.objects.bulk_update(alerts_to_update, ['is_active', 'condition_met_since'])
            logger.info(f"Updated state for {len(alerts_to_update)} alerts for user: {user.username}")

        if not is_remaining_alerts:
            disable_user_task_if_needed(user)
            logger.info(f"All alerts for user {user.username} are now inactive. The periodic task will continue to run but will do nothing until a new alert is activated.")

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found in check_user_alerts. The periodic task should be disabled manually.")
    except Exception as exc:
        logger.error(f"An unexpected error occurred in check_user_alerts for user {user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, user_id, triggered_alert_ids):
    """
    A Celery task to send an email notification to a SINGLE user for their
    recently triggered alerts.
    """
    logger.info(f"Starting task: send_email_notification for user_id: {user_id}")
    if not triggered_alert_ids:
        logger.warning("send_email_notification called with no triggered_alert_ids.")
        return

    try:
        user = User.objects.get(pk=user_id)
        if not user.email:
            logger.warning(f"User {user.username} (ID: {user_id}) has no email address. Skipping.")
            return

        alerts = TriggeredAlert.objects.filter(pk__in=triggered_alert_ids, user=user).select_related('alert', 'alert__company')
        if not alerts:
            logger.warning(f"No valid triggered alerts found for user {user_id} with IDs {triggered_alert_ids}.")
            return

        subject = f"StockWatcher Alert: {len(alerts)} of your alerts have triggered!"
        context = {'user': user, 'alerts': alerts}
        plain_text_message = render_to_string('alerts/triggered_alert_email.txt', context)
        html_message = render_to_string('alerts/triggered_alert_email.html', context)
        
        send_mail(
            subject=subject,
            message=plain_text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Successfully sent email to {user.username} for {len(alerts)} alerts.")

    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found. Cannot send email.")
    except smtplib.SMTPException as exc:
        logger.error(f"SMTP error sending email to user {user_id}: {exc}")
        raise self.retry(exc=exc)
    except Exception as exc:
        logger.error(f"An unexpected error in send_email_notification for user {user_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)
