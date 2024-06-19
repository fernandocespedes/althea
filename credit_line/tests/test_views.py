from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine, CreditLineAdjustment
from credit_line.api.serializers import CreditLineSerializer
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta


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


class CreditLineSetup:
    @staticmethod
    def setup_credit_line(cls):
        cls.credit_line = CreditLine.objects.create(
            credit_limit=Decimal("5000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            user=cls.user,
            status="pending",
        )


class CreditLineAdjustmentCreateTests(BaseTest, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        CreditLineSetup.setup_credit_line(cls)

    def test_create_adjustment_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("5500.00"),
            "new_end_date": (timezone.now() + timedelta(days=400)).date(),
            "reason": "Increase due to good standing.",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CreditLineAdjustment.objects.count(), 1)

    def test_create_adjustment_as_regular_user_invalid(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("5500.00"),
            "new_end_date": timezone.now().date() + timedelta(days=400),
            "reason": "Unauthorized to perform this action.",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_adjustment_nonexistent_credit_line(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create", kwargs={"pk": 999}
        )  # 999 does not exist
        data = {
            "new_credit_limit": Decimal("5500.00"),
            "new_end_date": timezone.now().date() + timedelta(days=400),
            "reason": "Credit Line 999 does not exist.",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_adjustment_invalid_data(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("-100.00"),  # Invalid value
            "reason": "",  # Missing reason
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access(self):
        self.client.logout()
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("5500.00"),
            "new_end_date": timezone.now().date() + timedelta(days=400),
            "reason": "Only authenticated staff can access this endpoint",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_new_credit_limit_validation_error(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("-100.00"),  # Invalid value
            "reason": "Improper limit",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_credit_limit", response.data)

    def test_new_end_date_validation_error(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("5000.00"),
            "new_end_date": timezone.now().date()
            - timedelta(days=1),  # before start date
            "reason": "Improper limit",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_end_date", response.data)

    def test_reject_datetime_in_date_field(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": self.credit_line.pk},
        )
        data = {
            "new_end_date": timezone.now(),
            "reason": "Testing datetime rejection",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_end_date", response.data)

    def test_adjustment_for_newly_created_credit_line(self):
        new_credit_line = CreditLine.objects.create(
            credit_limit=Decimal("5000000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            user=self.superuser,
            status="pending",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_create",
            kwargs={"pk": new_credit_line.pk},
        )
        data = {
            "new_credit_limit": Decimal("6000.00"),
            "reason": "Adjustment for new credit line",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class CreditLineAdjustmentStatusUpdateTests(BaseTest, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        CreditLineSetup.setup_credit_line(cls)

    def setUp(self):
        super().setUp()
        self.adjustment = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            previous_credit_limit=Decimal("3000"),
            new_credit_limit=Decimal("4000"),
            previous_end_date=timezone.now().date() + timedelta(days=30),
            new_end_date=timezone.now().date() + timedelta(days=60),
            reason="Adjusting limit and end date.",
        )

    def test_update_adjustment_status_as_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse(
            "credit_line_api:credit_line_adjustment_status_update",
            kwargs={"pk": self.adjustment.pk},
        )
        data = {"adjustment_status": "approved"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "approved")

    def test_update_adjustment_status_as_admin_invalid(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_status_update",
            kwargs={"pk": self.adjustment.pk},
        )
        data = {"adjustment_status": "approved"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "pending_review")

    def test_update_adjustment_status_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_status_update",
            kwargs={"pk": self.adjustment.pk},
        )
        data = {"adjustment_status": "approved"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_nonexistent_adjustment_status(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse(
            "credit_line_api:credit_line_adjustment_status_update",
            kwargs={"pk": 999},
        )
        data = {"adjustment_status": "approved"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_adjustment_status_invalid_data(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse(
            "credit_line_api:credit_line_adjustment_status_update",
            kwargs={"pk": self.adjustment.pk},
        )
        data = {"adjustment_status": "invalid_status"}  # Invalid status
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreditLineAdjustmentListTests(BaseTest, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        CreditLineSetup.setup_credit_line(cls)

    def setUp(self):
        super().setUp()
        self.adjustment = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            previous_credit_limit=Decimal("3000"),
            new_credit_limit=Decimal("4000"),
            previous_end_date=timezone.now().date() + timedelta(days=30),
            new_end_date=timezone.now().date() + timedelta(days=60),
            reason="Adjusting limit and end date.",
            adjustment_status="pending_review",
        )

    def test_list_adjustments_as_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("credit_line_api:credit_line_adjustments_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)

    def test_list_adjustments_as_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("credit_line_api:credit_line_adjustments_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_adjustments_unauthenticated(self):
        self.client.logout()
        url = reverse("credit_line_api:credit_line_adjustments_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_adjustments_nonexistent_credit_line(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("credit_line_api:credit_line_adjustments_admin_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreditLineAdjustmentDetailTests(BaseTest, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        CreditLineSetup.setup_credit_line(cls)

    def setUp(self):
        super().setUp()
        self.adjustment = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            previous_credit_limit=Decimal("3000"),
            new_credit_limit=Decimal("4000"),
            previous_end_date=timezone.now().date() + timedelta(days=30),
            new_end_date=timezone.now().date() + timedelta(days=60),
            reason="Adjusting limit and end date.",
            adjustment_status="pending_review",
        )

    def test_retrieve_adjustment_by_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse(
            "credit_line_api:credit_line_adjustment_detail", args=[self.adjustment.id]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.adjustment.id)

    def test_retrieve_adjustment_by_admin_user(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_detail", args=[self.adjustment.id]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.adjustment.id)

    def test_retrieve_adjustment_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "credit_line_api:credit_line_adjustment_detail", args=[self.adjustment.id]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_nonexistent_adjustment(self):
        self.client.force_authenticate(user=self.superuser)
        nonexistent_id = self.adjustment.id + 100
        url = reverse(
            "credit_line_api:credit_line_adjustment_detail", args=[nonexistent_id]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_adjustment_detail_content_accuracy(self):
        self.client.force_authenticate(user=self.superuser)
        url = reverse(
            "credit_line_api:credit_line_adjustment_detail", args=[self.adjustment.id]
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = [
            "id",
            "credit_line_id",
            "previous_credit_limit",
            "new_credit_limit",
            "previous_end_date",
            "new_end_date",
            "previous_currency",
            "new_currency",
            "adjustment_date",
            "adjustment_status",
            "reason",
        ]

        for field in expected_fields:
            self.assertIn(field, response.data)

        self.assertEqual(
            response.data["new_credit_limit"], f"{self.adjustment.new_credit_limit:.2f}"
        )
        self.assertEqual(response.data["reason"], self.adjustment.reason)

    def test_adjustment_detail_unauthenticated_access(self):
        self.client.logout()
        url = reverse(
            "credit_line_api:credit_line_adjustment_detail", args=[self.adjustment.id]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
