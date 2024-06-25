from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from decimal import Decimal
from django.utils import timezone
from credit_subline.api.serializers import (
    CreditSublineSerializer,
    CreditAmountAdjustmentSerializer,
    CreditAmountAdjustmentStatusSerializer,
    InterestRateAdjustmentSerializer,
    InterestRateAdjustmentStatusSerializer,
    CreditSublineStatusAdjustmentSerializer,
    CreditSublineStatusAdjustmentStatusSerializer,
)
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from credit_subline.tests.base_test import BaseCreditSublineViewTests


class CreditSublineSerializerTest(BaseTest):
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

        cls.credit_subline_data = {
            "credit_line": cls.credit_line.id,
            "subline_type": cls.credit_type.id,
            "subline_amount": Decimal("5000.00"),
            "amount_disbursed": Decimal("1000.00"),
            "outstanding_balance": Decimal("4000.00"),
            "interest_rate": Decimal("0.05"),
            "status": "pending",
        }

    def test_serializer_with_valid_data(self):
        serializer = CreditSublineSerializer(
            data=self.credit_subline_data, context={"credit_line": self.credit_line}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subline = serializer.save()
        self.assertEqual(
            subline.subline_amount, self.credit_subline_data["subline_amount"]
        )
        self.assertEqual(subline.credit_line, self.credit_line)
        # Ensure credit_line is correctly associated

    def test_serializer_with_negative_values(self):
        negative_values_data = self.credit_subline_data.copy()
        negative_values_data["subline_amount"] = Decimal("-5000.00")
        serializer = CreditSublineSerializer(data=negative_values_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("subline_amount", serializer.errors)
        self.assertEqual(
            serializer.errors["subline_amount"][0],
            "subline_amount must be greater than 0.",
        )

    def test_serializer_with_invalid_interest_rate(self):
        invalid_interest_data = self.credit_subline_data.copy()
        invalid_interest_data["interest_rate"] = Decimal("-0.05")
        serializer = CreditSublineSerializer(data=invalid_interest_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("interest_rate", serializer.errors)
        self.assertEqual(
            serializer.errors["interest_rate"][0],
            "interest_rate must be greater than 0.",
        )

    def test_serializer_with_invalid_amount(self):
        credit_subline_invalid_data = self.credit_subline_data.copy()
        credit_subline_invalid_data["subline_amount"] = Decimal(
            "5000000000000.00"
        )  # Invalid
        serializer = CreditSublineSerializer(data=credit_subline_invalid_data)
        valid = serializer.is_valid()
        self.assertFalse(valid)
        self.assertIn(
            "subline_amount", serializer.errors
        )  # Check if subline_amount error is present
        # Optionally check for a specific error message
        self.assertTrue(
            any(
                "Ensure that there are no more than 12 digits in total." in error
                for error in serializer.errors.get("subline_amount", [])
            )
        )

    def test_serializer_with_negative_interest_rate_invalid(self):
        credit_subline_invalid_data = self.credit_subline_data.copy()
        credit_subline_invalid_data["interest_rate"] = Decimal("-5.5")  # Invalid
        serializer = CreditSublineSerializer(data=credit_subline_invalid_data)
        valid = serializer.is_valid()
        self.assertFalse(valid)
        self.assertIn("interest_rate", serializer.errors)
        self.assertTrue(
            any(
                "interest_rate must be greater than 0." in error
                for error in serializer.errors.get("interest_rate", [])
            )
        )

    def test_credit_line_association(self):
        serializer = CreditSublineSerializer(
            data=self.credit_subline_data, context={"credit_line": self.credit_line}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subline = serializer.save()
        self.assertEqual(subline.credit_line, self.credit_line)


class CreditAmountAdjustmentSerializerTest(BaseCreditSublineViewTests):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("10000.00"),
            interest_rate=Decimal("0.25"),
            status="active",
        )

    def test_valid_credit_amount_adjustment_creation(self):
        adjustment_data = {
            "adjusted_amount": Decimal("500000"),
            "reason_for_adjustment": "Adjustment for testing",
            "adjustment_status": "pending_review",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = CreditAmountAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(adjustment.credit_subline.id, self.credit_subline.id)
        self.assertEqual(adjustment.adjusted_amount, Decimal("500000"))
        self.assertEqual(adjustment.reason_for_adjustment, "Adjustment for testing")
        self.assertEqual(serializer.data["credit_subline_id"], self.credit_subline.id)

    def test_initial_amount_populated_correctly(self):
        # Create an adjustment instance to test the populated fields
        adjustment_instance = CreditAmountAdjustment.objects.create(
            credit_subline=self.credit_subline,
            adjusted_amount=Decimal("800000"),
            reason_for_adjustment="Annual review adjustment",
            adjustment_status="pending_review",
        )
        serializer = CreditAmountAdjustmentSerializer(instance=adjustment_instance)
        expected_values = {
            "initial_amount": self.credit_subline.subline_amount,
        }
        for field, expected_value in expected_values.items():
            self.assertEqual(
                str(getattr(adjustment_instance, field)), str(serializer.data[field])
            )

    def test_credit_subline_association_on_creation(self):
        adjustment_data = {
            "adjusted_amount": Decimal("500000"),
            "reason_for_adjustment": "Adjustment for market changes",
            "adjustment_status": "pending_review",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = CreditAmountAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(adjustment.credit_subline.id, self.credit_subline.id)

    def test_credit_amount_edge_cases(self):
        """
        Test for edge cases in credit amount, such as extremely high values.
        """
        adjustment_data = {
            "credit_subline": self.credit_subline.id,
            "adjusted_amount": Decimal("100000000000000.00"),  # invalid amount
            "reason_for_adjustment": "Adjustment for market changes",
            "adjustment_status": "pending_review",
        }
        serializer = CreditAmountAdjustmentSerializer(data=adjustment_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("adjusted_amount", serializer.errors)


class CreditAmountAdjustmentStatusSerializerTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("50000.00"),
            interest_rate=Decimal("0.25"),
            status="active",
        )

        cls.adjustment_instance = CreditAmountAdjustment.objects.create(
            credit_subline=cls.credit_subline,
            adjusted_amount=Decimal("80000"),
            reason_for_adjustment="Annual review adjustment",
            adjustment_status="approved",
        )

    def test_approved_to_implemented_status_update(self):
        today_date = timezone.now().date()
        data = {"adjustment_status": "implemented"}
        serializer = CreditAmountAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_instance = serializer.save()
        self.assertEqual(updated_instance.effective_date, today_date)

    def test_invalid_status_transition(self):
        # Ensuring the initial status is "implemented" to test the invalid transition
        self.adjustment_instance.adjustment_status = "implemented"
        self.adjustment_instance.save()

        data = {"adjustment_status": "approved"}  # Invalid transition
        serializer = CreditAmountAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("adjustment_status", serializer.errors)

    def test_idempotent_status_update(self):
        # Setting the adjustment_status to a value it already has
        initial_status = self.adjustment_instance.adjustment_status
        data = {"adjustment_status": initial_status}
        serializer = CreditAmountAdjustmentStatusSerializer(
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
                updated_instance.effective_date,
                self.adjustment_instance.effective_date,
            )


class InterestRateAdjustmentSerializerTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("10000.00"),
            interest_rate=Decimal("0.25"),
            status="active",
        )

    def test_valid_interest_rate_adjustment_creation(self):
        adjustment_data = {
            "adjusted_interest_rate": Decimal("0.50"),
            "reason_for_adjustment": "Market fluctuation adjustment",
            "adjustment_status": "pending_review",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = InterestRateAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(adjustment.credit_subline.id, self.credit_subline.id)
        self.assertEqual(adjustment.adjusted_interest_rate, Decimal("0.50"))
        self.assertEqual(
            adjustment.reason_for_adjustment, "Market fluctuation adjustment"
        )
        self.assertEqual(serializer.data["credit_subline_id"], self.credit_subline.id)

    def test_negative_interest_rate_validation(self):
        adjustment_data = {
            "adjusted_interest_rate": Decimal("-0.25"),  # invalid interest rate
            "reason_for_adjustment": "Incorrect entry",
            "adjustment_status": "pending_review",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = InterestRateAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("adjusted_interest_rate", serializer.errors)

    def test_interest_rate_adjustment_without_subline_context(self):
        adjustment_data = {
            "adjusted_interest_rate": Decimal("0.35"),
            "reason_for_adjustment": "Adjustment for compliance",
            "adjustment_status": "pending_review",
        }
        serializer = InterestRateAdjustmentSerializer(data=adjustment_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("credit_subline", serializer.errors)

    def test_interest_rate_edge_cases(self):
        """
        Test for edge cases in interest rate, such as unreasonably high values.
        """
        adjustment_data = {
            "adjusted_interest_rate": Decimal(
                "100.00"
            ),  # Potentially invalid edge case
            "reason_for_adjustment": "Test for high value",
            "adjustment_status": "pending_review",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = InterestRateAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class InterestRateAdjustmentStatusSerializerTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("10000.00"),
            interest_rate=Decimal("0.25"),
            status="active",
        )

        cls.adjustment_instance = InterestRateAdjustment.objects.create(
            credit_subline=cls.credit_subline,
            adjusted_interest_rate=Decimal("30.00"),
            reason_for_adjustment="Annual review adjustment",
            adjustment_status="approved",
        )

    def test_approved_to_implemented_status_update(self):
        today_date = timezone.now().date()
        data = {"adjustment_status": "implemented"}
        serializer = InterestRateAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_instance = serializer.save()
        self.assertEqual(updated_instance.effective_date, today_date)

    def test_invalid_status_transition(self):
        # Ensuring the initial status is "implemented" to test the invalid transition
        self.adjustment_instance.adjustment_status = "implemented"
        self.adjustment_instance.save()

        data = {"adjustment_status": "approved"}  # Invalid transition
        serializer = InterestRateAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("adjustment_status", serializer.errors)

    def test_idempotent_status_update(self):
        # Setting the adjustment_status to a value it already has
        initial_status = self.adjustment_instance.adjustment_status
        data = {"adjustment_status": initial_status}
        serializer = InterestRateAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid, serializer.errors)
        if is_valid:
            updated_instance = serializer.save()
            self.assertEqual(updated_instance.adjustment_status, initial_status)
            # verify other fields are unchanged
            self.assertEqual(
                updated_instance.effective_date,
                self.adjustment_instance.effective_date,
            )


class CreditSublineStatusAdjustmentSerializerTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("10000.00"),
            interest_rate=Decimal("0.25"),
            status="pending",
        )

    def test_credit_subline_status_adjustment_creation(self):
        adjustment_data = {
            "adjusted_status": "active",
            "reason_for_adjustment": "Whatever reason for adjustment",
            "adjustment_status": "pending_review",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = CreditSublineStatusAdjustmentSerializer(
            data=adjustment_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(adjustment.credit_subline.id, self.credit_subline.id)
        self.assertEqual(adjustment.adjusted_status, "active")
        self.assertEqual(
            adjustment.reason_for_adjustment, "Whatever reason for adjustment"
        )
        self.assertEqual(serializer.data["credit_subline_id"], self.credit_subline.id)

    def test_valid_status_transition_on_update(self):
        data = {
            "adjusted_status": "active",
            "reason_for_adjustment": "Valid status update",
        }
        serializer = CreditSublineStatusAdjustmentSerializer(
            context={"credit_subline": self.credit_subline},
            data=data,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(
            adjustment.adjusted_status,
            "active",
            "Adjusted status should be set to 'active'.",
        )

    def test_valid_status_transition_from_pending_to_active(self):
        initial_data = {
            "adjusted_status": "pending",
            "reason_for_adjustment": "Setting status to pending",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = CreditSublineStatusAdjustmentSerializer(
            data=initial_data, context=context
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        adjustment = serializer.save()
        self.assertEqual(
            adjustment.adjusted_status,
            "pending",
            "Initial adjusted status should be 'pending'.",
        )

        # Step 2: Update the same adjustment to change new_status to "approved"
        update_data = {
            "adjusted_status": "pending",
            "reason_for_adjustment": "Setting status to pending",
        }
        update_serializer = CreditSublineStatusAdjustmentSerializer(
            data=update_data, context=context
        )
        self.assertTrue(update_serializer.is_valid(), update_serializer.errors)
        update_serializer.save()

    def test_invalid_status_transition(self):
        self.credit_subline.status = "active"
        self.credit_subline.save()

        data = {
            "adjusted_status": "pending",
            "reason_for_adjustment": "Invalid status update attempt",
        }
        context = {"credit_subline": self.credit_subline}
        serializer = CreditSublineStatusAdjustmentSerializer(data=data, context=context)
        is_valid = serializer.is_valid()
        self.assertFalse(
            is_valid, "Transition from 'active' to 'pending' should be invalid."
        )
        if not is_valid:
            self.assertIn(
                "adjusted_status",
                serializer.errors,
                "Expected validation error for invalid status transition not found.",
            )

    def test_credit_subline_status_adjustment_without_subline_context(self):
        adjustment_data = {
            "adjusted_status": "active",
            "reason_for_adjustment": "Adjustment for compliance",
            "adjustment_status": "pending_review",
        }
        serializer = CreditSublineStatusAdjustmentSerializer(data=adjustment_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("credit_subline", serializer.errors)


class CreditSublineStatusAdjustmentStatusSerializerTest(BaseCreditSublineViewTests):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=Decimal("50000.00"),
            interest_rate=Decimal("0.25"),
            status="pending",
        )

        cls.adjustment_instance = CreditSublineStatusAdjustment.objects.create(
            credit_subline=cls.credit_subline,
            adjusted_status="active",
            reason_for_adjustment="Annual review adjustment",
            adjustment_status="approved",
        )

    def test_approved_to_implemented_status_update(self):
        today_date = timezone.now().date()
        data = {"adjustment_status": "implemented"}
        serializer = CreditSublineStatusAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_instance = serializer.save()
        self.assertEqual(updated_instance.effective_date, today_date)

    def test_invalid_status_transition(self):
        # Ensuring the initial status is "implemented" to test the invalid transition
        self.adjustment_instance.adjustment_status = "implemented"
        self.adjustment_instance.save()

        data = {"adjustment_status": "approved"}  # Invalid transition
        serializer = CreditSublineStatusAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("adjustment_status", serializer.errors)

    def test_idempotent_status_update(self):
        # Setting the adjustment_status to a value it already has
        initial_status = self.adjustment_instance.adjustment_status
        data = {"adjustment_status": initial_status}
        serializer = CreditSublineStatusAdjustmentStatusSerializer(
            instance=self.adjustment_instance, data=data, partial=True
        )
        is_valid = serializer.is_valid()

        self.assertTrue(is_valid, serializer.errors)
        if is_valid:
            updated_instance = serializer.save()
            self.assertEqual(updated_instance.adjustment_status, initial_status)
            # verify other fields are unchanged
            self.assertEqual(
                updated_instance.effective_date,
                self.adjustment_instance.effective_date,
            )
