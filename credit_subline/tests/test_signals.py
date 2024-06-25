from credit_subline.tests.base_test import BaseCreditSublineViewTests
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from credit_subline.signals import (
    update_credit_subline_amount_on_approval,
    update_credit_subline_interest_rate_on_approval,
    update_credit_subline_status_on_approval,
)
from decimal import Decimal
from unittest.mock import patch
from django.utils import timezone


class CreditSublineAdjustmentSignalTests(BaseCreditSublineViewTests):
    def setUp(self):
        super().setUp()

        # Create a CreditSubline instance
        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_amount=Decimal("50000"),
            interest_rate=Decimal("5.0"),
            status="pending",
        )

    def test_update_credit_subline_amount_on_approval(self):
        # Prepare the CreditAmountAdjustment instance
        amount_adjustment = CreditAmountAdjustment(
            credit_subline=self.credit_subline,
            initial_amount=self.credit_subline.subline_amount,
            adjusted_amount=Decimal("60000"),
            adjustment_status="approved",  # This triggers the update
            reason_for_adjustment="Increase in credit amount",
        )

        # Mocking the on_commit to immediately execute the callback
        with patch("django.db.transaction.on_commit") as mock_on_commit:
            mock_on_commit.side_effect = lambda func: func()

            # Directly call the signal handler logic
            update_credit_subline_amount_on_approval(
                sender=CreditAmountAdjustment, instance=amount_adjustment, created=False
            )

        # Fetch the updated instance from the database
        self.credit_subline.refresh_from_db()

        # Assert the subline_amount has been updated correctly
        self.assertEqual(self.credit_subline.subline_amount, Decimal("60000"))

        # Assert the adjustment_status and effective_date are set correctly
        amount_adjustment.refresh_from_db()
        self.assertEqual(amount_adjustment.adjustment_status, "implemented")
        self.assertEqual(amount_adjustment.effective_date, timezone.now().date())

    def test_no_update_when_status_not_approved(self):
        # Prepare another CreditAmountAdjustment instance with a different status
        amount_adjustment = CreditAmountAdjustment(
            credit_subline=self.credit_subline,
            initial_amount=self.credit_subline.subline_amount,
            adjusted_amount=Decimal("70000"),
            adjustment_status="pending_review",  # This should not trigger the update
            reason_for_adjustment="Attempted increase in credit amount",
        )

        # Attempt to call the signal handler logic without changing the status to "approved"
        update_credit_subline_amount_on_approval(
            sender=CreditAmountAdjustment, instance=amount_adjustment, created=False
        )

        # Fetch the updated instance from the database
        self.credit_subline.refresh_from_db()

        # Assert the subline_amount remains unchanged
        self.assertNotEqual(self.credit_subline.subline_amount, Decimal("70000"))

    def test_update_credit_subline_interest_rate_on_approval(self):
        # Prepare the InterestRateAdjustment instance
        interest_rate_adjustment = InterestRateAdjustment(
            credit_subline=self.credit_subline,
            initial_interest_rate=self.credit_subline.interest_rate,
            adjusted_interest_rate=Decimal("10.0"),
            adjustment_status="approved",  # This triggers the update
            reason_for_adjustment="Increase in interest rate",
        )

        # Mocking the on_commit to immediately execute the callback
        with patch("django.db.transaction.on_commit") as mock_on_commit:
            mock_on_commit.side_effect = lambda func: func()

            # Directly call the signal handler logic
            update_credit_subline_interest_rate_on_approval(
                sender=InterestRateAdjustment,
                instance=interest_rate_adjustment,
                created=False,
            )

        # Fetch the updated instance from the database
        self.credit_subline.refresh_from_db()

        # Assert the subline.interest_rate has been updated correctly
        self.assertEqual(
            self.credit_subline.interest_rate, (Decimal("10.0") / Decimal("100"))
        )

        # Assert the adjustment_status and effective_date are set correctly
        interest_rate_adjustment.refresh_from_db()
        self.assertEqual(interest_rate_adjustment.adjustment_status, "implemented")
        self.assertEqual(interest_rate_adjustment.effective_date, timezone.now().date())

    def test_no_update_when_status_not_approved_interest_rate(self):
        # Prepare another InterestRateAdjustment instance with a different status
        interest_rate_adjustment = InterestRateAdjustment(
            credit_subline=self.credit_subline,
            initial_interest_rate=self.credit_subline.interest_rate,
            adjusted_interest_rate=Decimal("10.0"),
            adjustment_status="pending_review",  # This should not trigger the update
            reason_for_adjustment="Attempted increase in credit interest rate",
        )

        # Attempt to call the signal handler logic without changing the status to "approved"
        update_credit_subline_amount_on_approval(
            sender=InterestRateAdjustment,
            instance=interest_rate_adjustment,
            created=False,
        )

        # Fetch the updated instance from the database
        self.credit_subline.refresh_from_db()

        # Assert the subline_interest_rate remains unchanged
        self.assertNotEqual(
            self.credit_subline.interest_rate, (Decimal("10.0") / Decimal("100"))
        )

    def test_update_credit_subline_status_on_approval(self):
        # Prepare the CreditSublineStatusAdjustment instance
        credit_subline_status_adjustment = CreditSublineStatusAdjustment(
            credit_subline=self.credit_subline,
            initial_status=self.credit_subline.status,
            adjusted_status="active",
            adjustment_status="approved",  # This triggers the update
            reason_for_adjustment="set credit subline status to active",
        )

        # Mocking the on_commit to immediately execute the callback
        with patch("django.db.transaction.on_commit") as mock_on_commit:
            mock_on_commit.side_effect = lambda func: func()

            # Directly call the signal handler logic
            update_credit_subline_status_on_approval(
                sender=InterestRateAdjustment,
                instance=credit_subline_status_adjustment,
                created=False,
            )

        # Fetch the updated instance from the database
        self.credit_subline.refresh_from_db()

        # Assert the subline.status has been updated correctly
        self.assertEqual(self.credit_subline.status, "active")

        # Assert the adjustment_status and effective_date are set correctly
        credit_subline_status_adjustment.refresh_from_db()
        self.assertEqual(
            credit_subline_status_adjustment.adjustment_status, "implemented"
        )
        self.assertEqual(
            credit_subline_status_adjustment.effective_date, timezone.now().date()
        )

    def test_no_update_when_status_not_approved_credit_subline_status(self):
        # Prepare another CreditSublineStatusAdjustment instance with a different status
        credit_subline_status_adjustment = CreditSublineStatusAdjustment(
            credit_subline=self.credit_subline,
            initial_status=self.credit_subline.status,
            adjusted_status="active",
            adjustment_status="pending_review",  # This should not trigger the update
            reason_for_adjustment="Attempted to set status to active",
        )

        # Attempt to call the signal handler logic without changing the status to "approved"
        update_credit_subline_status_on_approval(
            sender=InterestRateAdjustment,
            instance=credit_subline_status_adjustment,
            created=False,
        )

        # Fetch the updated instance from the database
        self.credit_subline.refresh_from_db()

        # Assert the subline.status remains unchanged
        self.assertNotEqual(self.credit_subline.status, "active")
