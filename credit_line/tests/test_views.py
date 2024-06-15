from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from credit_line.api.serializers import CreditLineSerializer


class CreditLineViewsTest(BaseTest, APITestCase):
    def setUp(self):
        super().setUp()
        self.credit_line_data = {
            "credit_limit": 50000.00,
            "currency": "mxn",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "user": self.user,
        }
        self.credit_line = CreditLine.objects.create(**self.credit_line_data)
        self.admin_user = self.superuser
        self.client.force_authenticate(user=self.user)

    def test_get_credit_line_authenticated_user(self):
        url = reverse(
            "credit_line_api:get_credit_line", kwargs={"pk": self.credit_line.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = CreditLineSerializer(self.credit_line)
        self.assertEqual(response.data, serializer.data)

    def test_get_credit_line_not_found(self):
        url = reverse("credit_line_api:get_credit_line", kwargs={"pk": 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Credit line not found.")

    def test_get_credit_line_unauthenticated(self):
        self.client.logout()
        url = reverse(
            "credit_line_api:get_credit_line", kwargs={"pk": self.credit_line.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_credit_lines_admin_list(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("credit_line_api:credit_lines_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) > 0)

    def test_credit_lines_admin_list_pagination(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("credit_line_api:credit_lines_admin_list")
        response = self.client.get(url, {"page": 1, "page_size": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("count", response.data)

    def test_credit_lines_admin_list_filter_status(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("credit_line_api:credit_lines_admin_list")
        response = self.client.get(url, {"status": "pending"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["status"], "pending")

    def test_credit_lines_admin_list_filter_user(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("credit_line_api:credit_lines_admin_list")
        response = self.client.get(url, {"user": self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["user"], self.user.id)

    def test_credit_lines_admin_list_unauthenticated(self):
        self.client.logout()
        url = reverse("credit_line_api:credit_lines_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_credit_lines_admin_list_non_admin_user(self):
        url = reverse("credit_line_api:credit_lines_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
