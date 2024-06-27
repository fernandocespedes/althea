from credit_subline.tests.base_test import BaseCreditSublineViewTests
from credit_subline.models import CreditSubline
from decimal import Decimal
from django.utils import timezone
from loan_management.api.serializers import (
    LoanTermSerializer,
    UpdateLoanTermStatusSerializer,
)
from loan_management.models import LoanTerm


class LoanTermSerializerTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="active",
        )

        cls.loan_term_data = {
            "term_length": 12,
            "repayment_frequency": "monthly",
            "payment_due_day": 15,
            "start_date": timezone.now().date(),
            "status": "pending",  # default status
        }

    def test_serializer_with_valid_data(self):
        serializer = LoanTermSerializer(
            data=self.loan_term_data, context={"credit_subline": self.credit_subline}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        loan_term = serializer.save()
        self.assertEqual(loan_term.term_length, self.loan_term_data["term_length"])
        self.assertEqual(
            loan_term.repayment_frequency, self.loan_term_data["repayment_frequency"]
        )
        self.assertEqual(
            loan_term.payment_due_day, self.loan_term_data["payment_due_day"]
        )
        self.assertEqual(loan_term.credit_subline, self.credit_subline)

    def test_serializer_with_invalid_payment_due_day(self):
        invalid_data = self.loan_term_data.copy()
        invalid_data["payment_due_day"] = 32
        serializer = LoanTermSerializer(
            data=invalid_data, context={"credit_subline": self.credit_subline}
        )
        self.assertFalse(serializer.is_valid())

    def test_serializer_with_negative_term_length(self):
        invalid_data = self.loan_term_data.copy()
        invalid_data["term_length"] = -12
        serializer = LoanTermSerializer(
            data=invalid_data, context={"credit_subline": self.credit_subline}
        )
        valid = serializer.is_valid()
        self.assertFalse(valid)
        self.assertIn("term_length", serializer.errors)

    def test_serializer_with_unrecognized_repayment_frequency(self):
        invalid_data = self.loan_term_data.copy()
        invalid_data["repayment_frequency"] = "yearly"
        serializer = LoanTermSerializer(
            data=invalid_data, context={"credit_subline": self.credit_subline}
        )
        valid = serializer.is_valid()
        self.assertFalse(valid)
        self.assertIn("repayment_frequency", serializer.errors)

    def test_credit_subline_association(self):
        serializer = LoanTermSerializer(
            data=self.loan_term_data, context={"credit_subline": self.credit_subline}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        loan_term = serializer.save()
        self.assertEqual(loan_term.credit_subline, self.credit_subline)

    def test_read_only_status_field(self):
        serializer = LoanTermSerializer(
            data={**self.loan_term_data, "credit_subline": self.credit_subline.id},
            context={"credit_subline": self.credit_subline},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        loan_term = serializer.save()
        self.assertEqual(loan_term.status, "pending")
        update_data = {**self.loan_term_data, "status": "approved"}
        serializer = LoanTermSerializer(
            loan_term,
            data=update_data,
            partial=True,
            context={"credit_subline": self.credit_subline},
        )
        serializer.is_valid()

        if serializer.is_valid():
            serializer.save()

        loan_term.refresh_from_db()

        # Assert that the status remains unchanged
        self.assertEqual(
            loan_term.status, "pending", "Status should not change as it is read-only"
        )

    def test_serializer_includes_status_field(self):
        serializer = LoanTermSerializer(
            data={**self.loan_term_data, "credit_subline": self.credit_subline.id},
            context={"credit_subline": self.credit_subline},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        loan_term = serializer.save()
        serializer = LoanTermSerializer(loan_term)
        self.assertIn("status", serializer.data)
        self.assertEqual(serializer.data["status"], "pending")

    def test_prevent_duplicate_loan_term_for_credit_subline(self):
        serializer = LoanTermSerializer(
            data=self.loan_term_data, context={"credit_subline": self.credit_subline}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()

        second_serializer = LoanTermSerializer(
            data=self.loan_term_data, context={"credit_subline": self.credit_subline}
        )
        self.assertFalse(second_serializer.is_valid())
        self.assertIn("credit_subline", second_serializer.errors)
        self.assertEqual(
            second_serializer.errors["credit_subline"][0],
            "A LoanTerm already exists for this CreditSubline.",
        )


class UpdateLoanTermStatusSerializerTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="active",
        )

        cls.credit_subline_2 = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="active",
        )

        cls.loan_term = LoanTerm.objects.create(
            credit_subline=cls.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
            status="pending",
        )

        cls.loan_term_data = {
            "credit_subline": cls.credit_subline_2,
            "term_length": 12,
            "repayment_frequency": "monthly",
            "payment_due_day": 15,
            "start_date": timezone.now().date(),
            "status": "pending",
        }

    def test_valid_status_transition(self):
        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term, data={"status": "approved"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_loan_term = serializer.save()
        self.assertEqual(updated_loan_term.status, "approved")

    def test_invalid_status_transition_from_rejected(self):

        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term, data={"status": "rejected"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term, data={"status": "approved"}
        )
        self.assertFalse(
            serializer.is_valid(),
            "Transition from 'rejected' to 'approved' should be invalid.",
        )
        if serializer.errors:
            self.assertIn(
                "status",
                serializer.errors,
                "There should be an error message for the 'status' field.",
            )
            self.assertTrue(
                any(
                    "Cannot transition from rejected to approved" in error
                    for error in serializer.errors["status"]
                ),
                "Error message should clearly state that the transition is not allowed.",
            )

    def test_status_idempotency(self):
        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term, data={"status": "pending"}
        )
        self.assertTrue(
            serializer.is_valid(),
            "Serializer should be valid when re-submitting the same status.",
        )
        updated_loan_term = serializer.save()
        self.assertEqual(
            updated_loan_term.status,
            "pending",
            "Idempotent update should not change the status.",
        )

    def test_transition_from_approved(self):
        self.loan_term.status = "approved"
        self.loan_term.save()
        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term, data={"status": "pending"}
        )
        self.assertFalse(serializer.is_valid())

    def test_exception_on_creation_attempt(self):
        serializer = UpdateLoanTermStatusSerializer(data=self.loan_term_data)
        self.assertFalse(serializer.is_valid())
        with self.assertRaises(AssertionError):
            serializer.save()

    def test_non_existent_status(self):
        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term,
            data={"status": "doesnt_exist"},  # Invalid status choice
        )
        self.assertFalse(
            serializer.is_valid(),
            "Serializer should be invalid when given a non-existent status.",
        )
        if serializer.errors:
            self.assertIn(
                "status",
                serializer.errors,
                "There should be an error message for the 'status' field.",
            )
            self.assertTrue(
                any(
                    "not a valid choice" in error
                    for error in serializer.errors["status"]
                ),
                "Error message should indicate a non-valid choice for 'status'.",
            )

    def test_read_only_field_update_attempt(self):
        initial_credit_subline_id = self.loan_term.credit_subline.id
        new_credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=Decimal("250000"),
            interest_rate=7.0,
            status="active",
        )

        data = {
            "status": "approved",
            "credit_subline": new_credit_subline.id,  # should be ignored
        }
        serializer = UpdateLoanTermStatusSerializer(
            instance=self.loan_term, data=data, partial=True
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.loan_term.refresh_from_db()

        # Check that 'credit_subline' has not changed
        self.assertEqual(
            self.loan_term.credit_subline.id,
            initial_credit_subline_id,
            "The credit_subline should not have changed.",
        )

        self.assertNotEqual(
            self.loan_term.credit_subline.id,
            new_credit_subline.id,
            "credit_subline should remain unchanged despite the update attempt.",
        )
