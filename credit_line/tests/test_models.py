from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine, CreditLineAdjustment
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class CreditLineTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.credit_line_data = {
            "credit_limit": Decimal("50000.00"),
            "currency": "mxn",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "status": "pending",
            "user": self.user,
        }

    def test_create_credit_line(self):
        credit_line = CreditLine.objects.create(**self.credit_line_data)
        self.assertEqual(
            credit_line.credit_limit, self.credit_line_data["credit_limit"]
        )
        self.assertEqual(credit_line.currency, self.credit_line_data["currency"])
        self.assertEqual(
            str(credit_line.start_date), self.credit_line_data["start_date"]
        )
        self.assertEqual(str(credit_line.end_date), self.credit_line_data["end_date"])
        self.assertEqual(credit_line.status, self.credit_line_data["status"])
        self.assertEqual(credit_line.user, self.credit_line_data["user"])

    def test_credit_limit_must_be_positive(self):
        self.credit_line_data["credit_limit"] = -1000.00
        with self.assertRaises(ValidationError):
            credit_line = CreditLine(**self.credit_line_data)
            credit_line.full_clean()

    def test_credit_limit_max_digits(self):
        self.credit_line_data["credit_limit"] = 100000000000.00
        with self.assertRaises(ValidationError):
            credit_line = CreditLine(**self.credit_line_data)
            credit_line.full_clean()

    def test_start_date_before_end_date(self):
        self.credit_line_data["start_date"] = "2025-01-01"
        self.credit_line_data["end_date"] = "2024-01-01"
        with self.assertRaises(ValidationError):
            credit_line = CreditLine(**self.credit_line_data)
            credit_line.full_clean()

    def test_default_status(self):
        del self.credit_line_data["status"]
        credit_line = CreditLine.objects.create(**self.credit_line_data)
        self.assertEqual(credit_line.status, "pending")

    def test_default_currency(self):
        del self.credit_line_data["currency"]
        credit_line = CreditLine.objects.create(**self.credit_line_data)
        self.assertEqual(credit_line.currency, "mxn")

    def test_string_representation(self):
        credit_line = CreditLine.objects.create(**self.credit_line_data)
        self.assertEqual(
            str(credit_line),
            f"{self.user} - {self.credit_line_data['credit_limit']}",
        )

    def test_ordering(self):
        credit_line1 = CreditLine.objects.create(**self.credit_line_data)
        self.credit_line_data["credit_limit"] = 60000.00
        self.credit_line_data["user"] = self.inactive_user
        credit_line2 = CreditLine.objects.create(**self.credit_line_data)
        credit_lines = CreditLine.objects.all()
        self.assertEqual(credit_lines[0], credit_line2)
        self.assertEqual(credit_lines[1], credit_line1)

    def test_user_one_to_one_relationship(self):
        # Ensure a user can only have one credit line
        CreditLine.objects.create(**self.credit_line_data)
        with self.assertRaises(ValidationError):
            CreditLine.objects.create(**self.credit_line_data)

    def test_make_adjustment(self):
        credit_line = CreditLine.objects.create(
            credit_limit=2000000,
            currency="mxn",
            start_date=timezone.now().date() + timezone.timedelta(days=1),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            user=self.user,
            status="pending",
        )  # Create a CreditLine instance
        new_data = {
            "credit_limit": Decimal("500000"),  # A valid new credit limit
            "end_date": credit_line.start_date
            + timezone.timedelta(days=365),  # A valid new end date
            "status": "approved",  # A valid new status
            "currency": "mxn",  # A valid currency option
        }
        reason = "Increased due to the behavior of the customer."
        credit_line.make_adjustment(new_data, reason)

        # Assert that the CreditLine was updated
        self.assertEqual(credit_line.credit_limit, new_data["credit_limit"])
        self.assertEqual(credit_line.end_date, new_data["end_date"])
        self.assertEqual(credit_line.status, new_data["status"])
        self.assertEqual(credit_line.currency, new_data["currency"])

        # Assert that an adjustment record was created
        adjustment = CreditLineAdjustment.objects.get(credit_line=credit_line)
        self.assertEqual(adjustment.new_credit_limit, new_data["credit_limit"])
        self.assertEqual(adjustment.reason, reason)


class CreditLineAdjustmentTest(BaseTest):
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

    def create_adjustment_instance(self, **kwargs):
        defaults = {
            "credit_line": self.credit_line,
            "previous_credit_limit": self.credit_line.credit_limit,
            "new_credit_limit": Decimal("2000000"),
            "previous_end_date": self.credit_line.end_date,
            "new_end_date": self.credit_line.end_date + timezone.timedelta(days=30),
            "previous_status": self.credit_line.status,
            "new_status": "approved",
            "previous_currency": self.credit_line.currency,
            "new_currency": "mxn",
            "adjustment_date": timezone.now().date(),
            "reason": "Initial Adjustment",
        }
        defaults.update(kwargs)
        return CreditLineAdjustment(**defaults)

    def test_new_credit_limit_validation(self):
        adjustment = self.create_adjustment_instance(
            new_credit_limit=Decimal("-500000")
        )
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("new_credit_limit" in context.exception.message_dict)

    def test_new_credit_limit_digits_validation(self):
        adjustment = self.create_adjustment_instance(
            new_credit_limit=Decimal("10000000000000")
        )
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("new_credit_limit" in context.exception.message_dict)

    def test_new_end_date_validation(self):
        adjustment = self.create_adjustment_instance(
            new_end_date=self.credit_line.start_date - timezone.timedelta(days=1)
        )
        with self.assertRaises(ValidationError) as context:
            adjustment.full_clean()
        self.assertTrue("new_end_date" in context.exception.message_dict)

    def test_save_method_sets_previous_values_on_partial_update(self):
        adjustment = CreditLineAdjustment(
            credit_line=self.credit_line,
            new_credit_limit=Decimal("15000.00"),
            reason="Credit increase for good performance",
        )
        adjustment.save()
        self.assertEqual(
            adjustment.previous_credit_limit, self.credit_line.credit_limit
        )
        self.assertEqual(adjustment.previous_end_date, self.credit_line.end_date)
        self.assertEqual(adjustment.previous_status, self.credit_line.status)
        self.assertEqual(adjustment.previous_currency, self.credit_line.currency)

        self.assertEqual(adjustment.new_credit_limit, Decimal("15000.00"))
        self.assertIsNone(adjustment.new_end_date)
        self.assertIsNone(adjustment.new_status)
        self.assertIsNone(adjustment.new_currency)

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
        adjustment.adjustment_status = "pending_review"
        adjustment.save()
        adjustment.adjustment_status = "approved"
        adjustment.save()
        self.assertEqual(adjustment.adjustment_status, "approved")
