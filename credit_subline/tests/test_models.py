from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from credit_subline.tests.base_test import BaseCreditSublineViewTests
from credit_subline.utils import interest_rate_by_100


class CreditSublineModelTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.approved_credit_line = CreditLine.objects.create(
            credit_limit=Decimal("1000000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            status="approved",
            user=cls.user,
        )

        cls.pending_credit_line = CreditLine.objects.create(
            credit_limit=Decimal("1000000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            status="pending",
            user=cls.admin_user,
        )

    def test_credit_subline_creation_valid(self):
        """Test creating a valid CreditSubline instance."""
        subline = CreditSubline.objects.create(
            credit_line=self.approved_credit_line,
            subline_type=self.credit_type,
            subline_amount=1000,
            interest_rate=5.5,
            status="inactive",
        )
        self.assertIsInstance(subline, CreditSubline)

    def test_credit_subline_active_status_with_approved_credit_line(self):
        """Test CreditSubline can be active with an approved CreditLine."""
        subline = CreditSubline(
            credit_line=self.approved_credit_line,
            subline_type=self.credit_type,
            subline_amount=1000,
            interest_rate=5.5,
            status="active",
        )
        # Should not raise ValidationError
        subline.full_clean()

    def test_credit_subline_active_status_with_non_approved_credit_line(self):
        """Test CreditSubline cannot be active with a non-approved CreditLine."""
        subline = CreditSubline(
            credit_line=self.pending_credit_line,
            subline_type=self.credit_type,
            subline_amount=1000,
            interest_rate=5.5,
            status="active",
        )
        with self.assertRaises(ValidationError):
            subline.full_clean()

    def test_credit_subline_update_status(self):
        """Test updating CreditSubline status from inactive to active."""
        subline = CreditSubline.objects.create(
            credit_line=self.approved_credit_line,
            subline_type=self.credit_type,
            subline_amount=1000,
            interest_rate=5.5,
            status="inactive",
        )
        subline.status = "active"
        # Should not raise ValidationError as the credit line is approved
        subline.full_clean()

    def test_credit_subline_str_representation(self):
        """Test the string representation of a CreditSubline instance."""
        subline = CreditSubline(
            credit_line=self.approved_credit_line,
            subline_type=self.credit_type,
            subline_amount=1000,
            interest_rate=5.5,
            status="inactive",
        )
        expected_str = f"{self.credit_type} - 1000 - inactive"
        self.assertEqual(str(subline), expected_str)

    def test_interest_rate_percentage_conversion(self):
        """Interest rate provided as percentage should be converted to decimal."""
        subline = CreditSubline(
            credit_line=self.approved_credit_line,
            subline_type=self.credit_type,
            subline_amount=Decimal("5000.00"),
            amount_disbursed=Decimal("1000.00"),
            outstanding_balance=Decimal("4000.00"),
            interest_rate=Decimal("35.5"),  # percentage
            status="pending",
        )
        subline.save()

        self.assertEqual(subline.interest_rate, Decimal("0.355"))

    def test_interest_rate_decimal(self):
        """Interest rate provided as decimal remains unchanged."""
        subline = CreditSubline(
            credit_line=self.approved_credit_line,
            subline_type=self.credit_type,
            subline_amount=Decimal("5000.00"),
            amount_disbursed=Decimal("1000.00"),
            outstanding_balance=Decimal("4000.00"),
            interest_rate=Decimal("0.355"),  # decimal
            status="pending",
        )
        subline.save()

        self.assertEqual(subline.interest_rate, Decimal("0.355"))

    def test_interest_rate_negative_invalid(self):
        """Negative Interest rates should not be valid."""
        with self.assertRaises(ValidationError):
            subline = CreditSubline(
                credit_line=self.approved_credit_line,
                subline_type=self.credit_type,
                subline_amount=Decimal("5000.00"),
                amount_disbursed=Decimal("1000.00"),
                outstanding_balance=Decimal("4000.00"),
                interest_rate=Decimal("-35.5"),  # invalid
                status="pending",
            )
            subline.save()


class CreditAmountAdjustmentTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

    def create_adjustment_instance(self, **kwargs):
        defaults = {
            "credit_subline": self.credit_subline,
            "initial_amount": self.credit_subline.subline_amount,
            "adjusted_amount": Decimal("1000000"),
            "effective_date": timezone.now().date(),
            "reason_for_adjustment": "Some Amount adjustment reason",
            "adjustment_status": "pending_review",
        }
        defaults.update(kwargs)
        return CreditAmountAdjustment(**defaults)

    def test_new_amount_validation(self):
        adjustment = self.create_adjustment_instance(adjusted_amount=Decimal("-500000"))
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjusted_amount" in context.exception.message_dict)

    def test_new_amount_digits_validation(self):
        adjustment = self.create_adjustment_instance(
            adjusted_amount=Decimal("10000000000000")
        )
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjusted_amount" in context.exception.message_dict)

    def test_save_method_sets_previous_values_on_partial_update(self):
        # Create a CreditLineAdjustment instance with only new_credit_limit provided
        adjustment = CreditAmountAdjustment(
            credit_subline=self.credit_subline,
            adjusted_amount=Decimal("750000.00"),
            reason_for_adjustment="Credit increase for good performance",
        )

        # Call the save method to trigger the automatic setting of previous_ fields
        adjustment.save()

        # Check that initial_amount field was set correctly
        self.assertEqual(adjustment.initial_amount, self.credit_subline.subline_amount)

        # Check that only the new_credit_limit field was updated
        self.assertEqual(adjustment.adjusted_amount, Decimal("750000.00"))

    def test_adjustment_status_validation(self):
        # Test with a valid status
        adjustment = self.create_adjustment_instance(adjustment_status="approved")
        try:
            adjustment.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

        # Test with an invalid status
        adjustment = self.create_adjustment_instance(adjustment_status="invalid_status")
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjustment_status" in context.exception.message_dict)

    def test_adjustment_logic_based_on_status(self):

        adjustment = self.create_adjustment_instance(adjustment_status="pending_review")
        adjustment.save()

        adjustment.adjustment_status = "approved"
        adjustment.save()

    def test_adjustment_lifecycle(self):
        adjustment = self.create_adjustment_instance()
        # Start with a pending review
        adjustment.adjustment_status = "pending_review"
        adjustment.save()
        # Simulate approval
        adjustment.adjustment_status = "approved"
        adjustment.save()
        # Verifying the final state is as expected
        self.assertEqual(adjustment.adjustment_status, "approved")


class InterestRateAdjustmentTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

    def create_adjustment_instance(self, **kwargs):
        defaults = {
            "credit_subline": self.credit_subline,
            "initial_interest_rate": self.credit_subline.interest_rate,
            "adjusted_interest_rate": Decimal("17.5"),
            "effective_date": timezone.now().date(),
            "reason_for_adjustment": "Some Interest Rate adjustment reason",
            "adjustment_status": "pending_review",
        }
        defaults.update(kwargs)
        return InterestRateAdjustment(**defaults)

    def test_new_interest_rate_negative_validation(self):
        adjustment = self.create_adjustment_instance(
            adjusted_interest_rate=Decimal("-5.5")
        )
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjusted_interest_rate" in context.exception.message_dict)

    def test_save_method_sets_previous_values_on_partial_update(self):
        # Create a CreditLineAdjustment instance with only adjusted_interest_rate provided
        adjustment = InterestRateAdjustment(
            credit_subline=self.credit_subline,
            adjusted_interest_rate=Decimal("20.75"),
            reason_for_adjustment="Interest increase due to more risk",
        )

        # Call the save method to trigger the automatic setting of previous_ fields
        adjustment.save()

        # Check that initial_interest_rate field was set correctly
        self.assertEqual(
            adjustment.initial_interest_rate,
            interest_rate_by_100(self.credit_subline.interest_rate),
        )

        # Check that only the adjusted_interest_rate field was updated
        self.assertEqual(adjustment.adjusted_interest_rate, Decimal("20.75"))

    def test_adjustment_status_validation(self):
        # Test with a valid status
        adjustment = self.create_adjustment_instance(adjustment_status="approved")
        try:
            adjustment.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

        # Test with an invalid status
        adjustment = self.create_adjustment_instance(adjustment_status="invalid_status")
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjustment_status" in context.exception.message_dict)

    def test_adjustment_lifecycle(self):
        adjustment = self.create_adjustment_instance()
        # Start with a pending review
        adjustment.adjustment_status = "pending_review"
        adjustment.save()
        # Simulate approval
        adjustment.adjustment_status = "approved"
        adjustment.save()
        # Verifying the final state is as expected
        self.assertEqual(adjustment.adjustment_status, "approved")


class CreditSublineStatusAdjustmentTest(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="inactive",
        )

    def create_adjustment_instance(self, **kwargs):
        defaults = {
            "credit_subline": self.credit_subline,
            "initial_status": self.credit_subline.status,
            "adjusted_status": "active",
            "effective_date": timezone.now().date(),
            "reason_for_adjustment": "Some Status adjustment reason",
            "adjustment_status": "pending_review",
        }
        defaults.update(kwargs)
        return CreditSublineStatusAdjustment(**defaults)

    def test_save_method_sets_previous_values_on_partial_update(self):
        # instance with only adjusted_status provided
        adjustment = CreditSublineStatusAdjustment(
            credit_subline=self.credit_subline,
            adjusted_status="active",
            reason_for_adjustment="Status set to Active!",
        )

        # Call the save method to trigger the automatic setting of previous_ fields
        adjustment.save()

        # Check that initial_status field was set correctly
        self.assertEqual(
            adjustment.initial_status,
            self.credit_subline.status,
        )

        # Check that only the adjusted_status field was updated
        self.assertEqual(adjustment.adjusted_status, "active")

    def test_subline_status_validation(self):
        # Test with a valid ADJUSTMENT status
        adjustment = self.create_adjustment_instance(adjusted_status="active")
        try:
            adjustment.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

        # Test with an invalid subline status
        adjustment = self.create_adjustment_instance(
            adjusted_status="subline_invalid_status"
        )
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjusted_status" in context.exception.message_dict)

    def test_subline_status_lifecycle(self):
        adjustment = self.create_adjustment_instance()
        adjustment.adjusted_status = "pending"
        adjustment.save()
        # Simulate approval
        adjustment.adjusted_status = "active"
        adjustment.save()
        # Verifying the final state is as expected
        self.assertEqual(adjustment.adjusted_status, "active")

    def test_adjustment_status_validation(self):
        # Test with a valid ADJUSTMENT status
        adjustment = self.create_adjustment_instance(adjustment_status="approved")
        try:
            adjustment.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

        # Test with an invalid status
        adjustment = self.create_adjustment_instance(adjustment_status="invalid_status")
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("adjustment_status" in context.exception.message_dict)

    def test_adjustment_lifecycle(self):
        adjustment = self.create_adjustment_instance()
        # Start with a pending review
        adjustment.adjustment_status = "pending_review"
        adjustment.save()
        # Simulate approval
        adjustment.adjustment_status = "approved"
        adjustment.save()
        # Verifying the final state is as expected
        self.assertEqual(adjustment.adjustment_status, "approved")
