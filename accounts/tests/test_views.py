from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.tests.base_test import BaseTest


class UserViewTest(APITestCase, BaseTest):
    def test_user_login(self):
        # Manually activate the user for testing purposes
        self.user.is_active = True
        self.user.save()
        login_data = {
            "email": "phil@grateful.com",
            "password": "password123",
        }
        response = self.client.post(
            reverse("accounts_api:token_obtain_pair"), login_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
