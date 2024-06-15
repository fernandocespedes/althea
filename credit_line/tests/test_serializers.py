from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from credit_line.api.serializers import CreditLineSerializer
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
