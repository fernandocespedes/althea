from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

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
