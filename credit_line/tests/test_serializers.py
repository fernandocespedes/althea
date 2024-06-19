from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine, CreditLineAdjustment
from credit_line.api.serializers import (
    CreditLineSerializer,
    CreditLineAdjustmentSerializer,
    CreditLineAdjustmentStatusSerializer,
)
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase


class CreditLineSerializerTest(BaseTest, APITestCase):
    def setUp(self):
        super().setUp()
        self.valid_credit_line_data = {
            "credit_limit": 50000.00,
            "currency": "mxn",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "user": self.user.id,
        }

    def test_valid_credit_line_serialization(self):
        serializer = CreditLineSerializer(data=self.valid_credit_line_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["credit_limit"],
            self.valid_credit_line_data["credit_limit"],
        )
        self.assertEqual(
            serializer.validated_data["currency"],
            self.valid_credit_line_data["currency"],
        )
        self.assertEqual(
            str(serializer.validated_data["start_date"]),
            self.valid_credit_line_data["start_date"],
        )
        self.assertEqual(
            str(serializer.validated_data["end_date"]),
            self.valid_credit_line_data["end_date"],
        )
        self.assertEqual(
            serializer.validated_data["user"].id, self.valid_credit_line_data["user"]
        )

    def test_credit_limit_must_be_positive(self):
        self.valid_credit_line_data["credit_limit"] = -1000.00
        serializer = CreditLineSerializer(data=self.valid_credit_line_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("credit_limit", serializer.errors)
        self.assertEqual(
            serializer.errors["credit_limit"][0], "Credit limit must be greater than 0."
        )

    def test_credit_limit_max_digits(self):
        self.valid_credit_line_data["credit_limit"] = 100000000000.00
        serializer = CreditLineSerializer(data=self.valid_credit_line_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("credit_limit", serializer.errors)
        self.assertEqual(
            serializer.errors["credit_limit"][0],
            "Ensure that there are no more than 12 digits in total.",
        )

    def test_start_date_before_end_date(self):
        self.valid_credit_line_data["start_date"] = "2025-01-01"
        self.valid_credit_line_data["end_date"] = "2024-01-01"
        serializer = CreditLineSerializer(data=self.valid_credit_line_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            serializer.errors["non_field_errors"][0],
            "Start date must be before the end date.",
        )

    def test_default_values(self):
        del self.valid_credit_line_data["end_date"]
        del self.valid_credit_line_data["currency"]
        serializer = CreditLineSerializer(data=self.valid_credit_line_data)
        self.assertTrue(serializer.is_valid())
        credit_line = serializer.save()
        self.assertEqual(credit_line.currency, "mxn")
        self.assertEqual(credit_line.status, "pending")

    def test_read_only_fields(self):
        self.valid_credit_line_data["user"] = self.user
        credit_line = CreditLine.objects.create(**self.valid_credit_line_data)
        data = CreditLineSerializer(credit_line).data
        self.assertIn("id", data)
        self.assertIn("created", data)
        self.assertIn("status", data)
        self.assertTrue(data["id"])
        self.assertTrue(data["created"])
        self.assertEqual(data["status"], "pending")

    def test_create_credit_line(self):
        serializer = CreditLineSerializer(data=self.valid_credit_line_data)
        self.assertTrue(serializer.is_valid())
        credit_line = serializer.save()
        self.assertEqual(
            credit_line.credit_limit, self.valid_credit_line_data["credit_limit"]
        )
        self.assertEqual(credit_line.currency, self.valid_credit_line_data["currency"])
        self.assertEqual(
            str(credit_line.start_date), self.valid_credit_line_data["start_date"]
        )
        self.assertEqual(
            str(credit_line.end_date), self.valid_credit_line_data["end_date"]
        )
        self.assertEqual(credit_line.user.id, self.valid_credit_line_data["user"])

    def test_update_credit_line(self):
        self.valid_credit_line_data["user"] = self.user
        credit_line = CreditLine.objects.create(**self.valid_credit_line_data)
        updated_data = {
            "credit_limit": 60000.00,
            "currency": "mxn",
            "start_date": "2024-01-01",
            "end_date": "2026-01-01",
            "user": self.user.id,
        }
        serializer = CreditLineSerializer(credit_line, data=updated_data)
        self.assertTrue(serializer.is_valid())
        updated_credit_line = serializer.save()
        self.assertEqual(updated_credit_line.credit_limit, updated_data["credit_limit"])
        self.assertEqual(updated_credit_line.currency, updated_data["currency"])
        self.assertEqual(
            str(updated_credit_line.start_date), updated_data["start_date"]
        )
        self.assertEqual(str(updated_credit_line.end_date), updated_data["end_date"])
        self.assertEqual(updated_credit_line.user.id, updated_data["user"])


class CreditLineAdjustmentSerializerTest(BaseTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_line = CreditLine.objects.create(
            credit_limit=Decimal("1000000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            status="pending",
            user=cls.user,
        )

    def test_valid_credit_line_adjustment_creation(self):
        adjustment_data = {
            "new_credit_limit": Decimal("500000"),
            "new_end_date": timezone.now().date() + timezone.timedelta(days=180),
            "new_currency": "mxn",
            "reason": "Adjustment for testing",
            "adjustment_status": "pending_review",
        }
        context = {"credit_line": self.credit_line}
        serializer = CreditLineAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(adjustment.credit_line.id, self.credit_line.id)
        self.assertEqual(adjustment.new_credit_limit, Decimal("500000"))
        self.assertEqual(adjustment.reason, "Adjustment for testing")
        self.assertEqual(serializer.data["credit_line_id"], self.credit_line.id)

    def test_end_date_before_start_date_validation(self):
        adjustment_data = {
            "new_end_date": self.credit_line.start_date - timezone.timedelta(days=1),
            "reason": "Invalid end date test",
            "new_credit_limit": Decimal("500000"),
            "new_currency": "mxn",
            "adjustment_status": "pending_review",
        }
        context = {"credit_line": self.credit_line}
        serializer = CreditLineAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_end_date", serializer.errors)

    def test_previous_fields_populated_correctly(self):
        adjustment_instance = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            previous_credit_limit=self.credit_line.credit_limit,
            new_credit_limit=Decimal("800000"),
            previous_end_date=self.credit_line.end_date,
            new_end_date=timezone.now().date() + timezone.timedelta(days=360),
            previous_currency=self.credit_line.currency,
            new_currency="mxn",
            reason="Annual review adjustment",
            adjustment_date=timezone.now().date(),
            adjustment_status="pending_review",
        )
        serializer = CreditLineAdjustmentSerializer(instance=adjustment_instance)
        expected_values = {
            "previous_credit_limit": self.credit_line.credit_limit,
            "previous_end_date": self.credit_line.end_date,
            "previous_currency": self.credit_line.currency,
            "previous_status": self.credit_line.status,
        }
        for field, expected_value in expected_values.items():
            self.assertEqual(
                str(getattr(adjustment_instance, field)), str(serializer.data[field])
            )

    def test_credit_line_association_on_creation(self):
        adjustment_data = {
            "new_credit_limit": Decimal("500000"),
            "new_end_date": timezone.now().date() + timezone.timedelta(days=180),
            "new_currency": "mxn",
            "reason": "Adjustment for market changes",
            "adjustment_status": "pending_review",
        }
        context = {"credit_line": self.credit_line}
        serializer = CreditLineAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(adjustment.credit_line.id, self.credit_line.id)

    def test_credit_limit_edge_cases(self):
        adjustment_data = {
            "new_credit_limit": Decimal("100000000000000.00"),  # invalid limit
            "new_end_date": timezone.now().date() + timezone.timedelta(days=180),
            "new_currency": "mxn",
            "reason": "Adjustment for market changes",
            "adjustment_status": "pending_review",
        }
        context = {"credit_line": self.credit_line}
        serializer = CreditLineAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("new_credit_limit", serializer.errors)

    def test_valid_status_transition(self):
        adjustment_data = {
            "new_status": "approved",
            "reason": "Valid status transition test",
            "adjustment_status": "pending_review",
        }
        context = {"credit_line": self.credit_line}
        serializer = CreditLineAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_status_transition(self):
        # Set the status of the credit line to 'approved'
        self.credit_line.status = "approved"
        self.credit_line.save()

        # Create a CreditLineAdjustment instance
        adjustment_instance = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            new_credit_limit=Decimal("4000"),
            new_end_date=timezone.now().date() + timezone.timedelta(days=180),
            new_currency="mxn",
            reason="Initial adjustment setup",
            new_status="approved",  # Initial new status
        )

        # Attempt to change status to 'rejected' (which is invalid)
        adjustment_data = {
            "new_status": "rejected",
            "reason": "Invalid status transition test",
            "adjustment_status": "pending_review",
        }
        serializer = CreditLineAdjustmentSerializer(
            instance=adjustment_instance,
            data=adjustment_data,
            context={"credit_line": self.credit_line},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("new_status", serializer.errors)

    def test_idempotent_status_update(self):
        adjustment_instance = self.credit_line.adjustments.create(
            previous_status="pending",
            new_status="pending",
            reason="Initial status",
            adjustment_status="pending_review",
        )
        adjustment_data = {
            "new_status": "pending",
            "reason": "Idempotent status update test",
            "adjustment_status": "pending_review",
        }
        serializer = CreditLineAdjustmentSerializer(
            instance=adjustment_instance,
            data=adjustment_data,
            context={"credit_line": self.credit_line},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class CreditLineAdjustmentStatusSerializerTest(BaseTest):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_line = CreditLine.objects.create(
            credit_limit=Decimal("1000000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            status="pending",
            user=cls.user,
        )
        cls.adjustment_instance = CreditLineAdjustment.objects.create(
            credit_line=cls.credit_line,
            previous_credit_limit=cls.credit_line.credit_limit,
            new_credit_limit=Decimal("500000"),
            previous_end_date=cls.credit_line.end_date,
            new_end_date=timezone.now().date() + timezone.timedelta(days=180),
            previous_currency=cls.credit_line.currency,
            new_currency="mxn",
            reason="Initial adjustment setup",
            adjustment_date=timezone.now().date(),
            adjustment_status="pending_review",
        )

    def test_approved_to_implemented_status_update(self):
        self.adjustment_instance.adjustment_status = "approved"
        self.adjustment_instance.save()
        today_date = timezone.now().date()
        data = {
            "adjustment_status": "implemented",
            "reason": "Approved for implementation",
        }
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_instance = serializer.save()
        self.assertEqual(updated_instance.adjustment_date, today_date)

    def test_idempotent_status_update(self):
        initial_status = self.adjustment_instance.adjustment_status
        data = {"adjustment_status": initial_status, "reason": "No change"}
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        is_valid = serializer.is_valid()

        self.assertTrue(
            is_valid, serializer.errors
        )  # Validate serializer does not throw an error for idempotent operation
        if is_valid:
            updated_instance = serializer.save()
            self.assertEqual(updated_instance.adjustment_status, initial_status)
            # verify other fields are unchanged
            self.assertEqual(
                updated_instance.adjustment_date,
                self.adjustment_instance.adjustment_date,
            )

    def test_cl_status_adjustment_validation(self):
        data = {
            "adjustment_status": "approved",
            "reason": "Testing adjustment status validation",
        }
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_valid_status_transition_on_update(self):
        data = {"adjustment_status": "approved", "reason": "Valid status update"}
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        self.adjustment_instance.refresh_from_db()
        self.assertEqual(
            self.adjustment_instance.adjustment_status,
            "approved",
            "New status should be updated to 'approved'.",
        )

    def test_valid_status_transition_from_pending_to_approved(self):
        initial_data = {
            "adjustment_status": "pending_review",
            "reason": "Setting status to pending_review",
        }
        initial_serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance,
            data=initial_data,
            partial=True,
        )
        self.assertTrue(initial_serializer.is_valid(), initial_serializer.errors)
        initial_serializer.save()

        self.adjustment_instance.refresh_from_db()
        self.assertEqual(
            self.adjustment_instance.adjustment_status,
            "pending_review",
            "Initial status should be 'pending_review'.",
        )

        update_data = {
            "adjustment_status": "approved",
            "reason": "Updating status to approved",
        }
        update_serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance,
            data=update_data,
            partial=True,
        )
        self.assertTrue(update_serializer.is_valid(), update_serializer.errors)
        update_serializer.save()

    def test_invalid_status_transition_appr_pr(self):
        self.adjustment_instance.adjustment_status = "approved"
        self.adjustment_instance.save()

        data = {
            "adjustment_status": "pending_review",
            "reason": "Invalid status update attempt",
        }
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        is_valid = serializer.is_valid()
        self.assertFalse(
            is_valid,
            "Transition from 'approved' to 'pending_review' should be invalid.",
        )
        if not is_valid:
            self.assertIn(
                "adjustment_status",
                serializer.errors,
                "Expected validation error for invalid status transition not found.",
            )

    def test_invalid_status_transition_imp_appr(self):
        self.adjustment_instance.adjustment_status = "implemented"
        self.adjustment_instance.save()

        data = {"adjustment_status": "approved"}  # Invalid transition
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("adjustment_status", serializer.errors)

    def test_valid_credit_line_status_adjustment_creation(self):
        valid_data = {
            "adjustment_status": "approved",
            "reason": "Expanding credit limit and extending term",
        }
        serializer = CreditLineAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=valid_data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertIsNotNone(
            adjustment.id, "Adjustment should have been created successfully."
        )
        self.assertEqual(
            adjustment.adjustment_status,
            "approved",
            "New status should be set to 'approved'.",
        )
        self.assertEqual(adjustment.reason, "Expanding credit limit and extending term")
