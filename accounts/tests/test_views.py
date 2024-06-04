from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.tests.base_test import BaseTest
from django.contrib.auth import get_user_model

User = get_user_model()


class UserViewTest(APITestCase, BaseTest):
    def test_user_registration(self):
        data = {
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com",
            "username": "bob",
            "password": "Password321@",
        }
        response = self.client.post(reverse("accounts_api:register-user"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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

    def test_user_password_reset(self):
        """Test password reset for an active user."""
        request_data = {
            "email": "phil@grateful.com",
        }
        response = self.client.post(
            reverse("accounts_api:forgot-password"), request_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(
            "Password reset email sent successfully.", response.json()["message"]
        )

    def test_inactive_user_password_reset(self):
        """Test password reset for an inactive user."""
        request_data = {"email": "jerry@example.com"}
        response = self.client.post(
            reverse("accounts_api:forgot-password"), request_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "No active account with this email address found.",
            response.json()["message"],
        )

    def test_nonexistent_user_password_reset(self):
        """Test password reset for a nonexistent user."""
        request_data = {"email": "charlie@example.com"}
        response = self.client.post(
            reverse("accounts_api:forgot-password"), request_data
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "No active account with this email address found.",
            response.json()["message"],
        )

    def test_user_profile_access(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("accounts_api:user-profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

    def test_user_profile_update(self):
        updated_data = {
            "first_name": "Phil",
            "last_name": "Lesh",
            "email": "phil_base@grateful.com",
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            reverse("accounts_api:user-profile-update"), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "phil_base@grateful.com")

    def test_get_users_as_admin(self):
        # Create an superuser
        admin_user = User.objects.create_superuser(
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            username="adminuser",
            password="admin123",
        )
        self.client.force_authenticate(user=admin_user)
        response = self.client.get(reverse("accounts_api:users-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), User.objects.count())

    def test_get_users_as_non_admin(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("accounts_api:users-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
