from credit_subline.tests.base_test import BaseCreditSublineViewTests
from credit_subline.models import CreditSubline
from decimal import Decimal
from django.utils import timezone
from loan_management.models import LoanTerm
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class LoanTermViewTests(BaseCreditSublineViewTests, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("1000"),
            amount_disbursed=Decimal("500"),
            outstanding_balance=Decimal("500"),
            interest_rate=Decimal("0.05"),
            status="pending",
        )

        cls.credit_subline_2 = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("1000"),
            amount_disbursed=Decimal("500"),
            outstanding_balance=Decimal("500"),
            interest_rate=Decimal("0.05"),
            status="pending",
        )

        cls.data = {
            "term_length": 12,
            "repayment_frequency": "monthly",
            "payment_due_day": 15,
            "start_date": timezone.now().date(),
            "status": "pending",
        }

        cls.create_url = reverse(
            "loan_management_api:loan_term_create",
            kwargs={"subline_pk": cls.credit_subline.pk},
        )

        cls.loan_term = LoanTerm.objects.create(
            credit_subline=cls.credit_subline_2,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
            status="pending",
        )

        cls.status_update_url = reverse(
            "loan_management_api:loan_term_status_update",
            kwargs={"loan_term_pk": cls.loan_term.pk},
        )

        cls.get_url = reverse(
            "loan_management_api:loan_term_detail",
            kwargs={"loan_term_pk": cls.loan_term.pk},
        )

    def test_create_loan_term_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LoanTerm.objects.count(), 2)

    def test_create_loan_term_unauthorized(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_loan_term_anonymous(self):
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_loan_term_invalid_data(self):
        self.client.force_authenticate(user=self.admin_user)
        invalid_data = self.data.copy()
        invalid_data["repayment_frequency"] = "yearly"
        response = self.client.post(self.create_url, data=invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_loan_term_missing_field(self):
        self.client.force_authenticate(user=self.admin_user)
        missing_data = self.data.copy()
        del missing_data["repayment_frequency"]  # Missing required field
        response = self.client.post(self.create_url, data=missing_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_loan_term_with_existing_credit_subline(self):
        self.client.force_authenticate(user=self.admin_user)
        # Create the first LoanTerm successfully
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Attempt to create another LoanTerm with the same CreditSubline
        response = self.client.post(self.create_url, data=self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_error_msg = "A LoanTerm already exists for this CreditSubline."
        self.assertEqual(response.data["credit_subline"][0], expected_error_msg)

    def test_status_update_success(self):
        self.client.force_authenticate(user=self.superuser)
        data = {"status": "approved"}
        response = self.client.patch(self.status_update_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.loan_term.refresh_from_db()
        self.assertEqual(self.loan_term.status, "approved")

    def test_status_update_unauthorized(self):
        self.client.force_authenticate(user=self.user)
        data = {"status": "approved"}
        response = self.client.patch(self.status_update_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_status_update_admin_unauthorized(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {"status": "approved"}
        response = self.client.patch(self.status_update_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_status_transition(self):
        self.client.force_authenticate(user=self.superuser)
        self.loan_term.status = "approved"
        self.loan_term.save()

        data = {"status": "pending"}
        response = self.client.patch(self.status_update_url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot transition from approved to pending", str(response.data))

    def test_status_field_required(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(self.status_update_url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("The 'status' field is required.", str(response.data))

    def test_retrieve_loan_term_success_by_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.loan_term.id)

    def test_loan_term_retrieval_denied_for_non_admin_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_loan_term_not_found(self):
        self.client.force_authenticate(user=self.admin_user)
        non_existent_url = reverse(
            "loan_management_api:loan_term_detail", kwargs={"loan_term_pk": 99999}
        )
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertContains(
            response, "not found", status_code=status.HTTP_404_NOT_FOUND
        )

    def test_retrieve_loan_term_success_by_superuser(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.loan_term.id)
