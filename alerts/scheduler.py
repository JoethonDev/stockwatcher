import json
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django_celery_beat.models import PeriodicTask, IntervalSchedule

logger = logging.getLogger(__name__)

def create_or_enable_user_task(user: User):
    """
    Ensures a periodic task exists and is enabled for a user.

    This function is called when a user creates their first active alert.
    It creates a new task schedule if one doesn't exist, or re-enables
    a previously disabled one.
    """
    try:
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=settings.STOCK_INTERVAL_IN_MINUTES,
            period=IntervalSchedule.MINUTES,
        )
        task_name = f'check-alerts-for-user-{user.id}'
        
        task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                'interval': schedule,
                'task': 'alerts.tasks.check_user_alerts',
                'args': json.dumps([user.id]),
            }
        )

        if not created and not task.enabled:
            task.enabled = True
            task.save()
            logger.info(f"Re-enabled periodic task for user: {user.username}")
        elif created:
            logger.info(f"Created new periodic task for user: {user.username}")

    except Exception as e:
        logger.error(f"Error creating/enabling task for user {user.id}: {e}", exc_info=True)

def disable_user_task_if_needed(user: User):
    """
    Disables a user's periodic task if they have no active alerts remaining.

    This function is called when a user deletes or deactivates an alert.
    It prevents the scheduler from running unnecessary checks.
    """
    try:
        if not user.alerts.filter(is_active=True).exists():
            task_name = f'check-alerts-for-user-{user.id}'
            try:
                task = PeriodicTask.objects.get(name=task_name)
                task.enabled = False
                task.save()
                logger.info(f"Disabled periodic task for user {user.username} as they have no active alerts.")
            except PeriodicTask.DoesNotExist:
                logger.warning(f"No periodic task found for user {user.username} to disable; this is expected if all alerts were deleted.")
    except Exception as e:
        logger.error(f"Error disabling task for user {user.id}: {e}", exc_info=True)
