from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from .models import Company, Alert, TriggeredAlert
from users.utils import generate_tokens

class BaseAlertTestCase(APITestCase):
    """
    Base test case for the alerts app. Sets up reusable users, companies,
    and an authenticated API client.
    """
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')

        # Create companies
        self.company_aapl = Company.objects.create(stock_symbol='AAPL', current_price=150.0)
        self.company_goog = Company.objects.create(stock_symbol='GOOG', current_price=2800.0)

        # Create an API client and authenticate the primary user
        self.client = APIClient()
        self.authenticate_client(self.user)

    def authenticate_client(self, user):
        tokens = generate_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')

    def unauthenticate_client(self):
        self.client.credentials()


class CompanyEndpointTests(BaseAlertTestCase):
    """
    Tests for the public /api/alerts/companies/ endpoint.
    """
    def test_list_companies_unauthenticated(self):
        """
        Ensure even unauthenticated users can view the company list.
        """
        self.unauthenticate_client()
        response = self.client.get('/api/alerts/companies/')
        results = response.data['results']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['stock_symbol'], 'AAPL')


class AlertEndpointTests(BaseAlertTestCase):
    """
    Tests for creating, listing, deleting, and reactivating alerts.
    """
    def setUp(self):
        """
        Extend the base setup to include a pre-existing alert for the user.
        """
        super().setUp()
        self.alert = Alert.objects.create(
            user=self.user,
            company=self.company_aapl,
            alert_type=Alert.AlertType.PRICE_THRESHOLD,
            condition=Alert.TriggerCondition.GREATER_THAN,
            threshold=200.0
        )

    @patch('alerts.views.create_or_enable_user_task')
    def test_create_alert_success(self, mock_create_task):
        """
        Ensure an authenticated user can create a new alert.
        """
        data = {
            'company': self.company_goog.pk,
            'alert_type': 'PRICE_THRESHOLD',
            'condition': 'LT',
            'threshold': 2500.0,
        }
        response = self.client.post('/api/alerts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.user.alerts.count(), 2)
        mock_create_task.assert_called_once_with(self.user)

    def test_create_alert_fails_unauthenticated(self):
        """
        Ensure unauthenticated users cannot create alerts.
        """
        self.unauthenticate_client()
        data = {'company': self.company_goog.pk, 'threshold': 2500.0}
        response = self.client.post('/api/alerts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_alerts_for_authenticated_user(self):
        """
        Ensure a user can list only their own alerts.
        """
        # Create an alert for the other user that should not appear in the list
        Alert.objects.create(user=self.other_user, company=self.company_goog, threshold=3000)
        
        response = self.client.get('/api/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.alert.id)

    def test_list_alerts_with_filtering(self):
        """
        Test filtering alerts by 'is_active' status.
        """
        self.alert.is_active = False
        self.alert.save()
        
        # Filter for inactive alerts
        response = self.client.get('/api/alerts/?is_active=false')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # Filter for active alerts
        response = self.client.get('/api/alerts/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    @patch('alerts.views.disable_user_task_if_needed')
    def test_delete_alert_success(self, mock_disable_task):
        """
        Ensure a user can delete their own alert.
        """
        response = self.client.delete(f'/api/alerts/{self.alert.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.user.alerts.count(), 0)
        mock_disable_task.assert_called_once_with(self.user)

    def test_delete_alert_fails_for_other_user(self):
        """
        Ensure a user cannot delete an alert they do not own.
        """
        other_alert = Alert.objects.create(user=self.other_user, company=self.company_goog, threshold=1)
        response = self.client.delete(f'/api/alerts/{other_alert.id}/')
        # Should return 404 as the alert is not in the user's queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Alert.objects.filter(pk=other_alert.pk).exists())

    @patch('alerts.views.create_or_enable_user_task')
    def test_reactivate_alert_success(self, mock_create_task):
        """
        Ensure a user can reactivate an inactive alert.
        """
        self.alert.is_active = False
        self.alert.save()
        
        response = self.client.patch(f'/api/alerts/{self.alert.id}/reactivate/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.alert.refresh_from_db()
        self.assertTrue(self.alert.is_active)
        mock_create_task.assert_called_once_with(self.user)


class TriggeredAlertEndpointTests(BaseAlertTestCase):
    """
    Tests for the /api/alerts/triggered/ endpoint.
    """
    def setUp(self):
        """
        Extend the base setup to include a pre-existing alert for the user.
        """
        super().setUp()
        self.alert = Alert.objects.create(
            user=self.user,
            company=self.company_aapl,
            alert_type=Alert.AlertType.PRICE_THRESHOLD,
            condition=Alert.TriggerCondition.GREATER_THAN,
            threshold=200.0
        )
        
    def test_list_triggered_alerts(self):
        """
        Ensure a user can list their triggered alert history.
        """
        # Create triggered history for both users
        TriggeredAlert.objects.create(user=self.user, alert=self.alert)
        
        other_alert = Alert.objects.create(user=self.other_user, company=self.company_goog, threshold=1)
        TriggeredAlert.objects.create(user=self.other_user, alert=other_alert)

        response = self.client.get('/api/alerts/triggered/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['alert']['id'], self.alert.id)
