from rest_framework.test import APITestCase
from rest_framework import status
from credit_subline.models import CreditSubline
from credit_subline.tests.base_test import BaseCreditSublineViewTests
from decimal import Decimal
from django.urls import reverse


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
