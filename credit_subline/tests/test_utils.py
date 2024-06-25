from django.test import TestCase
from decimal import Decimal
from credit_subline.utils import interest_rate_by_100


class CalculateInitialInterestRateTest(TestCase):
    def test_calculate_initial_interest_rate(self):
        # Test case with a straightforward interest rate
        interest_rate = Decimal(".055")  # Representing 5.5%
        expected_initial_rate = Decimal("5.5")  # Expected result after multiplication
        calculated_rate = interest_rate_by_100(interest_rate)
        self.assertEqual(
            calculated_rate,
            expected_initial_rate,
            "The calculated initial interest rate should be correct.",
        )

        # Additional test case with a zero interest rate
        interest_rate_zero = Decimal("0.0")  # Representing 0%
        expected_initial_rate_zero = Decimal("0")  # Expected result is also 0
        calculated_rate_zero = interest_rate_by_100(interest_rate_zero)
        self.assertEqual(
            calculated_rate_zero,
            expected_initial_rate_zero,
            "The calculated initial interest rate for zero should be correct.",
        )

        # Additional test case with a more precise interest rate
        interest_rate_precise = Decimal("2.375")  # A more precise interest rate
        expected_initial_rate_precise = Decimal("237.5")
        calculated_rate_precise = interest_rate_by_100(interest_rate_precise)
        self.assertEqual(
            calculated_rate_precise,
            expected_initial_rate_precise,
            "The calculated initial interest rate for a precise value should be correct.",
        )
