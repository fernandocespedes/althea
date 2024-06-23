from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from decimal import Decimal
from django.utils import timezone
from credit_subline.api.serializers import (
    CreditSublineSerializer,
)


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
