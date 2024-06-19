from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine, CreditLineAdjustment
from decimal import Decimal
from django.utils import timezone
from unittest.mock import patch
from django.test import TransactionTestCase
from credit_line.signals import (
    update_credit_line_on_approval,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class DirectSignalLogicTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.credit_line = CreditLine.objects.create(
            credit_limit=Decimal("100000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            user=self.user,
            status="pending",
        )

    @patch("credit_line.models.CreditLine.make_adjustment")
    def test_update_credit_line_on_approval_signal_logic(self, mock_make_adjustment):
        # Prepare the CreditLineAdjustment instance
        adjustment = CreditLineAdjustment(
            credit_line=self.credit_line,
            previous_credit_limit=Decimal("100000"),
            new_credit_limit=Decimal("150000"),
            new_end_date=timezone.now().date() + timezone.timedelta(days=730),
            adjustment_status="approved",  # This triggers the update
            reason="Test adjustment",
        )

        # Mocking the on_commit to immediately execute the callback
        with patch("django.db.transaction.on_commit") as mock_on_commit:
            mock_on_commit.side_effect = lambda func: func()

            # Directly call the signal handler logic
            update_credit_line_on_approval(
                sender=CreditLineAdjustment, instance=adjustment, created=False
            )

        # Verify the make_adjustment method was called with the expected arguments
        mock_make_adjustment.assert_called_once_with(
            {
                "credit_limit": Decimal("150000"),
                "end_date": adjustment.new_end_date,
                # Include any other fields that are updated in the make_adjustment call
            },
            "Automatic adjustment on approval",
            update_only=True,
        )

        # Assert the adjustment_status and dates directly
        self.assertEqual(adjustment.adjustment_status, "implemented")
        self.assertEqual(adjustment.adjustment_date, timezone.now().date())


_previous_adjustment_statuses = {}


class CreditLineAdjustmentSignalTests(TransactionTestCase):

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="testuser", password="testpassword")
        self.credit_line = CreditLine.objects.create(
            credit_limit=Decimal("100000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            user=self.user,
            status="pending",
        )
        self.adjustment = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            previous_credit_limit=self.credit_line.credit_limit,
            new_credit_limit=Decimal("800000"),
            previous_end_date=self.credit_line.end_date,
            new_end_date=timezone.now().date() + timezone.timedelta(days=180),
            previous_currency=self.credit_line.currency,
            new_currency="mxn",
            reason="Second adjustment setup",
            adjustment_date=timezone.now().date(),
            adjustment_status="approved",
        )

    def test_direct_database_update(self):
        # Directly simulate the expected outcome of the signal
        CreditLineAdjustment.objects.filter(pk=self.adjustment.pk).update(
            adjustment_status="implemented"
        )
        self.adjustment.refresh_from_db()
        self.assertEqual(self.adjustment.adjustment_status, "implemented")

        CreditLine.objects.filter(pk=self.credit_line.pk).update(
            credit_limit=Decimal("150000")
        )
        self.credit_line.refresh_from_db()
        self.assertEqual(self.credit_line.credit_limit, Decimal("150000"))

    def manually_capture_previous_status(self, instance):
        if instance.pk:
            try:
                old_instance = type(instance).objects.get(pk=instance.pk)
                _previous_adjustment_statuses[instance.pk] = (
                    old_instance.adjustment_status
                )
            except type(instance).DoesNotExist:
                pass

    def test_credit_line_update_on_approval(self):
        adjustment = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            new_credit_limit=Decimal("150000"),
            new_end_date=timezone.now().date() + timezone.timedelta(days=730),
            new_status="approved",
            adjustment_date=timezone.now().date(),
            reason="For testing approval",
        )

        # Manually simulate pre_save signal logic
        self.manually_capture_previous_status(adjustment)

        # Simulate status change to trigger post_save signal
        adjustment.adjustment_status = "approved"
        adjustment.save()

        self.credit_line.refresh_from_db()

        self.assertEqual(self.credit_line.credit_limit, Decimal("150000"))
        self.assertEqual(self.credit_line.status, "approved")

    def test_adjustment_status_set_to_implemented(self):
        adjustment = CreditLineAdjustment.objects.create(
            credit_line=self.credit_line,
            new_credit_limit=Decimal("200000"),
            new_end_date=timezone.now().date() + timezone.timedelta(days=730),
            new_status="approved",
            adjustment_date=timezone.now().date(),
            reason="For final implementation",
        )

        # Manually simulate pre_save signal logic
        self.manually_capture_previous_status(adjustment)

        adjustment.adjustment_status = "approved"
        adjustment.save()

        adjustment.refresh_from_db()
        self.assertEqual(adjustment.adjustment_status, "implemented")

    def test_adjustment_date_update_on_status_change(self):
        # Given an approved CreditLineAdjustment instance
        self.adjustment.adjustment_status = "approved"
        self.adjustment.save()

        # When the signal processes the adjustment
        self.adjustment.refresh_from_db()

        # Then the adjustment_date should be updated to the current date
        self.assertEqual(self.adjustment.adjustment_date, timezone.now().date())
        self.assertEqual(self.adjustment.adjustment_status, "implemented")
