from rest_framework.test import APITestCase
from rest_framework import status
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from credit_subline.tests.base_test import BaseCreditSublineViewTests
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone


class CreateCreditSublineViewTests(BaseCreditSublineViewTests, APITestCase):
    def test_create_credit_subline_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.create_url, data=self.data, format="json")
        # print("response", response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CreditSubline.objects.count(), 1)

    def test_create_credit_subline_unauthorized(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_credit_subline_anonymous(self):
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_credit_subline_invalid_data(self):
        self.client.force_authenticate(user=self.admin_user)
        invalid_data = self.data.copy()
        invalid_data["subline_amount"] = "-1000.00"  # Invalid amount
        response = self.client.post(self.create_url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_credit_subline_missing_field(self):
        self.client.force_authenticate(user=self.admin_user)
        missing_data = self.data.copy()
        del missing_data["subline_amount"]  # Missing required field
        response = self.client.post(self.create_url, data=missing_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetCreditSublineViewTests(BaseCreditSublineViewTests, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for i in range(15):
            CreditSubline.objects.create(
                credit_line=cls.credit_line,
                subline_type=cls.credit_type,
                subline_amount=Decimal("1000") * (i + 1),
                amount_disbursed=Decimal("500") * (i + 1),
                outstanding_balance=Decimal("500") * (i + 1),
                interest_rate=Decimal("0.05"),
                status="pending" if i % 2 == 0 else "active",
            )

        cls.get_url = reverse(
            "credit_subline_api:get_account_credit_sublines",
            kwargs={"credit_line_pk": cls.credit_line.pk},
        )

    def test_credit_sublines_pagination(self):
        self.client.force_authenticate(user=self.admin_user)
        url = self.admin_list_url

        # Test default page size
        response = self.client.get(url)
        self.assertTrue("results" in response.data)
        self.assertEqual(len(response.data["results"]), 10)

        # Test custom page size
        response = self.client.get(f"{url}?page_size=5")
        self.assertEqual(len(response.data["results"]), 5)

        # Test max page size limit
        response = self.client.get(f"{url}?page_size=20")
        self.assertEqual(len(response.data["results"]), 15)

    def test_credit_sublines_list_data_integrity(self):
        self.client.force_authenticate(user=self.admin_user)
        url = self.admin_list_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertGreaterEqual(len(response.data["results"]), 1)

        credit_subline_data = response.data["results"][0]
        self.assertEqual(credit_subline_data["status"], "pending")
        self.assertTrue(Decimal(credit_subline_data["subline_amount"]) > 0)
        self.assertTrue(Decimal(credit_subline_data["interest_rate"]) > 0)

    def test_credit_sublines_list_access_control(self):
        # Attempt to access without authentication
        url = self.admin_list_url
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticate as a regular user (non-admin)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Authenticate as an admin user
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_credit_sublines_filter_by_status(self):
        self.client.force_authenticate(user=self.admin_user)
        url = f"{self.admin_list_url}?status=pending"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        for subline in response.data["results"]:
            self.assertEqual(subline["status"], "pending")

    def test_get_credit_subline_success(self):
        self.client.force_authenticate(user=self.user)
        credit_subline = CreditSubline.objects.first()
        url = reverse(
            "credit_subline_api:get_credit_subline", kwargs={"pk": credit_subline.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], credit_subline.id)

    def test_get_credit_subline_not_found(self):
        self.client.force_authenticate(user=self.user)
        credit_subline = CreditSubline.objects.first()
        url = reverse(
            "credit_subline_api:get_credit_subline",
            kwargs={"pk": credit_subline.pk + 700},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_credit_subline_unauthorized(self):
        credit_subline = CreditSubline.objects.first()
        url = reverse(
            "credit_subline_api:get_credit_subline", kwargs={"pk": credit_subline.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_credit_subline_forbidden(self):
        # another user tries to access other's info credit subline
        self.client.force_authenticate(user=self.admin_user)
        credit_subline = CreditSubline.objects.first()
        url = reverse(
            "credit_subline_api:get_credit_subline", kwargs={"pk": credit_subline.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_account_credit_sublines_success_user(self):
        CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=Decimal("1000"),
            amount_disbursed=Decimal("500"),
            outstanding_balance=Decimal("500"),
            interest_rate=Decimal("0.05"),
            status="pending",
        )
        # Authenticate as the user associated with the credit_line
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 16)

    def test_get_account_credit_sublines_unauthorized(self):
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_account_credit_sublines_not_found(self):
        self.client.force_authenticate(user=self.user)
        url = reverse(
            "credit_subline_api:get_account_credit_sublines",
            kwargs={"credit_line_pk": 99999},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CreditAmountAdjustmentViewTests(BaseCreditSublineViewTests, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

        self.data = {
            "adjusted_amount": Decimal("75000.00"),
            "reason_for_adjustment": "Increase due to good standing.",
        }

        # Create a single adjustment and set it up for use in tests
        adjustment_list = self.create_adjustments(1)
        self.adjustment = adjustment_list[0]

        # Prepare the URL for updating adjustment status
        self.update_url = reverse(
            "credit_subline_api:credit_amount_adjustment_status_update",
            kwargs={"adj_pk": self.adjustment.id},
        )

    def create_adjustments(self, count=1):
        """
        Helper method to create a specified number of CreditAmountAdjustment instances.
        """
        adjustments = [
            CreditAmountAdjustment.objects.create(
                credit_subline=self.credit_subline,
                adjusted_amount=Decimal("5000") + i,
                reason_for_adjustment=f"Adjustment reason {i}",
                adjustment_status="pending_review",
            )
            for i in range(count)
        ]
        return adjustments

    def test_create_adjustment_as_admin(self):
        # Test that an admin user can create an adjustment
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_amount_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CreditAmountAdjustment.objects.count(), 2)
        # the one created here + the setUp adjustment

    def test_create_adjustment_as_regular_user_invalid(self):

        self.client.force_authenticate(user=self.regular_user)
        url = reverse(
            "credit_subline_api:credit_amount_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_adjustment_nonexistent_credit_subline(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_amount_adjustment_create",
            kwargs={"subline_pk": 999},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_adjustment_invalid_data(self):
        # Test that creating an adjustment with invalid data returns an error
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_amount_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        inv_data = {
            "adjusted_amount": Decimal("-10000.00"),
            "reason_for_adjustment": "",  # Missing reason
        }
        response = self.client.post(url, inv_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason_for_adjustment", response.data)
        self.assertIn("adjusted_amount", response.data)

    def test_unauthenticated_access(self):
        # Test that unauthenticated requests are rejected
        url = reverse(
            "credit_subline_api:credit_amount_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adjustment_for_newly_created_credit_subline(self):
        new_credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_amount_adjustment_create",
            kwargs={"subline_pk": new_credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_status_update_by_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "approved")

    def test_status_update_by_non_superuser(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_update_without_superuser_privileges(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_transition(self):
        self.client.force_authenticate(user=self.superuser)
        self.adjustment.adjustment_status = "aporoved"
        self.adjustment.save()
        data = {"adjustment_status": "pending_review"}  # Invalid backward transition
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_update_without_body(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(self.update_url, {}, format="json")  # Empty data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_update_to_nonexistent_status(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "nonexistent_status"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("adjustment_status", response.data)

    def test_idempotent_status_update(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "pending_review"}  # Same as current status
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "pending_review")

    def test_effective_date_update_on_implementation(self):
        self.client.force_authenticate(user=self.superuser)
        self.adjustment.adjustment_status = "approved"
        self.adjustment.save()
        data = {"adjustment_status": "implemented"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "implemented")
        self.assertEqual(self.adjustment.effective_date, timezone.now().date())


class InterestRateAdjustmentViewTests(BaseCreditSublineViewTests, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

        self.data = {
            "adjusted_interest_rate": Decimal("32.00"),
            "reason_for_adjustment": "Increase due to more risk.",
        }

        # Create a single adjustment and set it up for use in tests
        adjustment_list = self.create_adjustments(1)
        self.adjustment = adjustment_list[0]

        # Prepare the URL for updating adjustment status
        self.update_url = reverse(
            "credit_subline_api:interest_rate_adjustment_status_update",
            kwargs={"adj_pk": self.adjustment.id},
        )

    def create_adjustments(self, count=1):
        """
        Helper method to create a specified number of InterestRateAdjustment instances.
        """
        adjustments = [
            InterestRateAdjustment.objects.create(
                credit_subline=self.credit_subline,
                adjusted_interest_rate=Decimal("7.5") + i,
                reason_for_adjustment=f"Adjustment reason {i}",
                adjustment_status="pending_review",
            )
            for i in range(count)
        ]
        return adjustments

    def test_create_adjustment_as_admin(self):
        # Test that an admin user can create an adjustment
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:interest_rate_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(InterestRateAdjustment.objects.count(), 2)
        # the one created here + the setUp adjustment

    def test_create_adjustment_as_regular_user_invalid(self):

        self.client.force_authenticate(user=self.regular_user)
        url = reverse(
            "credit_subline_api:interest_rate_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_adjustment_nonexistent_credit_subline(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:interest_rate_adjustment_create",
            kwargs={"subline_pk": 999},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_adjustment_invalid_data(self):
        # Test that creating an adjustment with invalid data returns an error
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:interest_rate_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        inv_data = {
            "adjusted_interest_rate": Decimal("-7.50"),
            "reason_for_adjustment": "",  # Missing reason
        }
        response = self.client.post(url, inv_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason_for_adjustment", response.data)
        self.assertIn("adjusted_interest_rate", response.data)

    def test_unauthenticated_access(self):
        # Test that unauthenticated requests are rejected
        url = reverse(
            "credit_subline_api:interest_rate_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adjustment_for_newly_created_credit_subline(self):
        new_credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:interest_rate_adjustment_create",
            kwargs={"subline_pk": new_credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_status_update_by_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "approved")

    def test_status_update_by_non_superuser(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_update_without_superuser_privileges(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_transition(self):
        self.client.force_authenticate(user=self.superuser)
        self.adjustment.adjustment_status = "aporoved"
        self.adjustment.save()
        data = {"adjustment_status": "pending_review"}  # Invalid backward transition
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_update_without_body(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(self.update_url, {}, format="json")  # Empty data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_update_to_nonexistent_status(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "nonexistent_status"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("adjustment_status", response.data)

    def test_idempotent_status_update(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "pending_review"}  # Same as current status
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "pending_review")

    def test_effective_date_update_on_implementation(self):
        self.client.force_authenticate(user=self.superuser)
        self.adjustment.adjustment_status = "approved"
        self.adjustment.save()
        data = {"adjustment_status": "implemented"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "implemented")
        self.assertEqual(self.adjustment.effective_date, timezone.now().date())


class CreditSublineStatusAdjustmentViewTests(BaseCreditSublineViewTests, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="pending",
        )

        adjustment_list = self.create_adjustments(1)
        self.adjustment = adjustment_list[0]

        self.data = {
            "adjusted_status": "active",
            "reason_for_adjustment": "Activated subline.",
        }

        self.update_url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_status_update",
            kwargs={"adj_pk": self.adjustment.id},
        )

    def create_adjustments(self, count=1):
        """
        Helper method to create a specified number of
        CreditSublineStatusAdjustment instances.
        """
        adjustments = [
            CreditSublineStatusAdjustment.objects.create(
                credit_subline=self.credit_subline,
                adjusted_status="active",
                reason_for_adjustment=f"Adjustment reason {i}",
                adjustment_status="pending_review",
            )
            for i in range(count)
        ]
        return adjustments

    def test_create_adjustment_as_admin(self):
        # Test that an admin user can create an adjustment
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CreditSublineStatusAdjustment.objects.count(), 2)
        # the one created here + the setUp adjustment

    def test_create_adjustment_as_regular_user_invalid(self):

        self.client.force_authenticate(user=self.regular_user)
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_adjustment_nonexistent_credit_subline(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": 999},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_adjustment_invalid_data(self):
        # Test that creating an adjustment with invalid data returns an error
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        inv_data = {
            "adjusted_status": "some_invented_status",
            "reason_for_adjustment": "",  # Missing reason
        }
        response = self.client.post(url, inv_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason_for_adjustment", response.data)
        self.assertIn("adjusted_status", response.data)

    def test_unauthenticated_access(self):
        # Test that unauthenticated requests are rejected
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adjustment_for_newly_created_credit_subline(self):
        new_credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="pending",
        )

        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": new_credit_subline.pk},
        )
        response = self.client.post(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_credit_subline_status_transition(self):
        self.client.force_authenticate(user=self.admin_user)
        self.credit_subline.status = "active"
        self.credit_subline.save()
        url = reverse(
            "credit_subline_api:credit_subline_status_adjustment_create",
            kwargs={"subline_pk": self.credit_subline.pk},
        )
        inv_transition_data = {
            "adjusted_status": "pending",
            "reason_for_adjustment": "Invalid transition",
        }
        response = self.client.post(url, inv_transition_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjustment_status_update_by_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "approved")

    def test_adjustment_status_update_by_non_superuser(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_adjustment_status_update_without_superuser_privileges(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {"adjustment_status": "approved"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_adjustment_status_transition(self):
        self.client.force_authenticate(user=self.superuser)
        self.adjustment.adjustment_status = "aporoved"
        self.adjustment.save()
        data = {"adjustment_status": "pending_review"}  # Invalid backward transition
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjustment_status_update_without_body(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(self.update_url, {}, format="json")  # Empty data
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjustment_status_update_to_nonexistent_status(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "nonexistent_status"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("adjustment_status", response.data)

    def test_idempotent_adjustment_status_update(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"adjustment_status": "pending_review"}  # Same as current status
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "pending_review")

    def test_effective_date_update_on_implementation(self):
        self.client.force_authenticate(user=self.superuser)
        self.adjustment.adjustment_status = "approved"
        self.adjustment.save()
        data = {"adjustment_status": "implemented"}
        response = self.client.patch(self.update_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "implemented")
        self.assertEqual(self.adjustment.effective_date, timezone.now().date())

    def test_credit_subline_activation_with_unapproved_credit_line(self):
        # Set the credit line's status to something other than 'approved'
        self.credit_line.status = "pending"
        self.credit_line.save()

        # Attempt to approve a CreditSublineStatusAdjustment
        # when the CreditLine's status is not 'approved'
        self.client.force_authenticate(user=self.superuser)
        adjustment_data = {
            "adjustment_status": "approved"
        }  # Attempt to approve the adjustment

        response = self.client.patch(self.update_url, adjustment_data, format="json")

        # Verify that the system prevents the status change and returns an error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(
            response.data["error"],
            "The CreditSubline cannot be set to active because "
            "the associated CreditLine's status is not approved.",
        )


class CreditSublineAdjustmentsAdminListTests(BaseCreditSublineViewTests, APITestCase):
    def setUp(self):
        super().setUp()

        self.client.force_authenticate(user=self.admin_user)

        for i in range(4):
            subline = CreditSubline.objects.create(
                credit_line=self.credit_line,
                subline_type=self.credit_type,
                subline_amount=Decimal("1000") * (i + 1),
                amount_disbursed=Decimal("500") * (i + 1),
                outstanding_balance=Decimal("500") * (i + 1),
                interest_rate=Decimal("5.0"),
                status="pending",
            )

            # For each CreditSubline, create different types of adjustments
            CreditAmountAdjustment.objects.create(
                credit_subline=subline,
                initial_amount=Decimal("1000") * (i + 1),
                adjusted_amount=Decimal("1500") * (i + 1),
                effective_date=timezone.now().date(),
                reason_for_adjustment="Adjustment due to performance #" + str(i),
                adjustment_status="pending_review",
            )

            InterestRateAdjustment.objects.create(
                credit_subline=subline,
                initial_interest_rate=Decimal("5.0"),
                adjusted_interest_rate=Decimal("4.5"),
                effective_date=timezone.now().date(),
                reason_for_adjustment="Reduced interest for customer loyalty #"
                + str(i),
                adjustment_status="pending_review",
            )

            CreditSublineStatusAdjustment.objects.create(
                credit_subline=subline,
                initial_status="pending",
                adjusted_status="active" if i % 2 == 0 else "inactive",
                effective_date=timezone.now().date() - timezone.timedelta(days=i),
                reason_for_adjustment="Review outcome #" + str(i),
                adjustment_status="pending_review",
            )

        self.url = reverse("credit_subline_api:credit_subline_adjustments_admin_list")

    def test_access_for_admin_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_for_regular_user(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_adjustments(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Initialize counters for each adjustment type
        adjustment_counts = {
            "amount": 0,
            "interest_rate": 0,
            "status": 0,
        }

        # Iterate over results and increment counters based on adjustment type
        for item in response.data["results"]:
            if item["adjustment_type"] == "amount":
                adjustment_counts["amount"] += 1
            elif item["adjustment_type"] == "interest_rate":
                adjustment_counts["interest_rate"] += 1
            elif item["adjustment_type"] == "status":
                adjustment_counts["status"] += 1

        # Ensure that each type of adjustment is present
        self.assertGreater(
            adjustment_counts["amount"], 0, "Should include amount adjustments"
        )
        self.assertGreater(
            adjustment_counts["interest_rate"],
            0,
            "Should include interest rate adjustments",
        )
        self.assertGreater(
            adjustment_counts["status"], 0, "Should include status adjustments"
        )

    def test_filter_by_adjustment_type_amount(self):
        response = self.client.get(self.url, {"type": "amount"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure only amount adjustments are returned
        for item in response.data["results"]:
            self.assertEqual(item["adjustment_type"], "amount")

    def test_filter_by_adjustment_type_interest_rate(self):
        response = self.client.get(self.url, {"type": "interest_rate"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["adjustment_type"], "interest_rate")

    def test_filter_by_adjustment_type_status(self):
        response = self.client.get(self.url, {"type": "status"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["adjustment_type"], "status")

    def test_invalid_adjustment_type_returns_all_adjustments(self):
        response = self.client.get(self.url, {"type": "invalid_type"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the response includes all types of adjustments.
        found_types = set()
        for item in response.data["results"]:
            found_types.add(item["adjustment_type"])

        # check all types are present in the response when an invalid type is requested.
        self.assertTrue("amount" in found_types)
        self.assertTrue("interest_rate" in found_types)
        self.assertTrue("status" in found_types)

    def test_adjustments_pagination(self):
        self.client.force_authenticate(user=self.admin_user)
        url = self.url

        # Test default page size
        response = self.client.get(url)
        self.assertTrue("results" in response.data)
        self.assertTrue(
            len(response.data["results"]) <= 10,
            "Default page size should not exceed 10 items",
        )

        # Test custom page size
        custom_page_size = 5
        response = self.client.get(f"{url}?page_size={custom_page_size}")
        self.assertEqual(
            len(response.data["results"]),
            custom_page_size,
            "Custom page size should match the requested size",
        )

    def test_adjustments_list_data_integrity(self):
        self.client.force_authenticate(user=self.admin_user)
        url = self.url

        # get a mix of different adjustments
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertGreaterEqual(
            len(response.data["results"]), 1, "Should return at least one adjustment"
        )

        # Verify the first adjustment in the list for expected fields and values
        adjustment = response.data["results"][0]
        self.assertIn(
            "adjustment_type", adjustment, "Adjustment should include the type"
        )
        self.assertIn(
            adjustment["adjustment_type"],
            ["amount", "interest_rate", "status"],
            "Adjustment type should be recognized",
        )

        # Additional checks based on the type of adjustment:
        if adjustment["adjustment_type"] == "amount":
            self.assertTrue(
                Decimal(adjustment["adjusted_amount"]) > 0,
                "Adjusted amount should be positive",
            )

    def test_adjustments_sorted_by_effective_date_across_types(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        self.assertTrue(
            len(results) > 1, "Should have multiple adjustments for sorting test"
        )
        previous_date = results[0]["effective_date"]
        for adjustment in results[1:]:
            current_date = adjustment["effective_date"]
            self.assertTrue(
                previous_date >= current_date,
                "Adjustments are not properly sorted by effective_date",
            )
            previous_date = current_date

    def test_filter_by_adjustment_status(self):
        known_status = "pending_review"
        response = self.client.get(self.url, {"adjustment_status": known_status})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that all returned adjustments have the specified status
        for item in response.data["results"]:
            self.assertEqual(
                item["adjustment_status"],
                known_status,
                "Adjustment does not match the specified status",
            )

    def test_filter_by_type_and_status(self):
        known_status = "pending_review"
        # Choose a type and ensure there are adjustments of this type with the known status
        adjustment_type = "amount"
        response = self.client.get(
            self.url, {"type": adjustment_type, "adjustment_status": known_status}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that adjustments returned match both filters
        for item in response.data["results"]:
            self.assertEqual(
                item["adjustment_type"],
                adjustment_type,
                "Adjustment does not match the specified type",
            )
            self.assertEqual(
                item["adjustment_status"],
                known_status,
                "Adjustment does not match the specified status",
            )

    def test_filter_by_invalid_adjustment_status(self):
        invalid_status = "nonexistent_status"
        response = self.client.get(self.url, {"adjustment_status": invalid_status})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The API returns an empty list for an invalid status
        self.assertEqual(
            len(response.data["results"]),
            0,
            "API should return an empty list for an invalid status",
        )

    def test_adjustment_response_structure(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            "results" in response.data and len(response.data["results"]) > 0,
            "No results returned",
        )

        # Check the first adjustment to verify if adjustment_status is present
        first_adjustment = response.data["results"][0]
        self.assertIn(
            "adjustment_status",
            first_adjustment,
            "Adjustment status is not present in the response",
        )


class CreditSublineAdjustmentDetailTests(BaseCreditSublineViewTests, APITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=Decimal("1000"),
            amount_disbursed=Decimal("500"),
            outstanding_balance=Decimal("500"),
            interest_rate=Decimal("5.0"),
            status="pending",
        )

        self.adjustment_amount = CreditAmountAdjustment.objects.create(
            credit_subline=self.credit_subline,
            initial_amount=Decimal("1000"),
            adjusted_amount=Decimal("1500"),
            effective_date=timezone.now().date(),
            reason_for_adjustment="Adjustment due to performance #",
            adjustment_status="pending_review",
        )

        self.adjustment_interest = InterestRateAdjustment.objects.create(
            credit_subline=self.credit_subline,
            initial_interest_rate=Decimal("5.0"),
            adjusted_interest_rate=Decimal("4.5"),
            effective_date=timezone.now().date(),
            reason_for_adjustment="Reduced interest for customer loyalty",
            adjustment_status="pending_review",
        )

        self.adjustment_status = CreditSublineStatusAdjustment.objects.create(
            credit_subline=self.credit_subline,
            initial_status="pending",
            adjusted_status="active",
            effective_date=timezone.now().date() - timezone.timedelta(days=1),
            reason_for_adjustment="Some testing reason",
            adjustment_status="pending_review",
        )

        self.url = reverse("credit_subline_api:credit_subline_adjustments_admin_list")

    def test_get_specific_amount_adjustment(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:get_credit_subline_adjustment",
            args=["amount", self.adjustment_amount.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.adjustment_amount.id)

    def test_get_specific_interest_adjustment(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:get_credit_subline_adjustment",
            args=["interest_rate", self.adjustment_interest.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.adjustment_interest.id)

    def test_get_specific_status_adjustment(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:get_credit_subline_adjustment",
            args=["status", self.adjustment_status.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.adjustment_status.id)

    def test_unauthorized_access(self):
        self.client.force_authenticate(user=self.regular_user)
        url = reverse(
            "credit_subline_api:get_credit_subline_adjustment",
            args=["amount", self.adjustment_amount.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_adjustment(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse(
            "credit_subline_api:get_credit_subline_adjustment", args=["amount", 99999]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
