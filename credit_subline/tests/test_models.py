from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from credit_subline.models import CreditSubline


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
