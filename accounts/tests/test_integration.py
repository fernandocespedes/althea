from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from accounts.api.utils import (
    account_token_generator,
)
from accounts.tests.base_test import BaseTest
import time
from rest_framework.test import APITestCase
from rest_framework import status


User = get_user_model()


class AccountActivationTest(APITestCase, BaseTest):
    def test_account_activation(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = account_token_generator.make_token(self.user)
        timestamp = int(time.time())
        url = reverse(
            "accounts_api:activate-account",
            kwargs={"uidb64": uid, "token": token, "timestamp": timestamp},
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)


class PasswordResetTest(APITestCase, BaseTest):
    def test_password_reset_confirm(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = account_token_generator.make_token(self.user)
        timestamp = int(time.time())
        url = reverse(
            "accounts_api:reset-password-confirm",
            kwargs={"uidb64": uid, "token": token, "timestamp": timestamp},
        )

        response = self.client.post(
            url,
            {"password": "Mynewpassword123@", "confirm_password": "Mynewpassword123@"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
