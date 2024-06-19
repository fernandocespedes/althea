from accounts.tests.base_test import BaseTest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from credit_origination.models import CreditRequest
from decimal import Decimal


User = get_user_model()


class IsSuperUserPermissionTests(BaseTest, APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            username="regularuser",
            password="Password123",
            first_name="Regular",
            last_name="User",
        )
        self.superuser = User.objects.create_superuser(
            email="super@example.com",
            username="superuser",
            password="Password123",
            first_name="Super",
            last_name="User",
        )

        self.credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
            status="pending",
        )

    def test_superuser_permission(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse(
            "credit_origination_api:credit_request_status_update",
            kwargs={"pk": self.credit_request.pk},
        )
        response = self.client.put(url, {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_regular_user_permission(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse(
            "credit_origination_api:credit_request_status_update",
            kwargs={"pk": self.credit_request.pk},
        )
        response = self.client.put(url, {"status": "approved"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_permission(self):
        url = reverse(
            "credit_origination_api:credit_request_status_update",
            kwargs={"pk": self.credit_request.pk},
        )
        response = self.client.put(url, {"status": "approved"}, format="json")
        self.assertEqual(
            response.status_code, 401
        )  # Expecting 401 Unauthorized for anonymous users
