from django.test import TestCase
import pandas as pd

from loan_management.finance_utils import (
    calculate_periodic_interest_rate,
    adjust_payment_date,
    generate_amortization_schedule,
)


class TestPeriodicInterestRate(TestCase):
    def test_periodic_interest_rate_monthly(self):
        self.assertEqual(calculate_periodic_interest_rate(0.12, "monthly"), 0.01)

    def test_periodic_interest_rate_biweekly(self):
        self.assertEqual(calculate_periodic_interest_rate(0.26, "biweekly"), 0.01)

    def test_periodic_interest_rate_bimonthly(self):
        self.assertEqual(calculate_periodic_interest_rate(0.12, "bimonthly"), 0.02)

    def test_periodic_interest_rate_quarterly(self):
        self.assertEqual(calculate_periodic_interest_rate(0.12, "quarterly"), 0.03)

    def test_periodic_interest_rate_zero_rate(self):
        self.assertEqual(calculate_periodic_interest_rate(0, "monthly"), 0)

    def test_periodic_interest_rate_negative_rate_invalid(self):
        with self.assertRaises(ValueError):
            calculate_periodic_interest_rate(-0.12, "monthly"), -0.01

    def test_periodic_interest_rate_greater_rate_invalid(self):
        with self.assertRaises(ValueError):
            calculate_periodic_interest_rate(12, "monthly"), 1

    def test_periodic_interest_rate_invalid_frequency(self):
        with self.assertRaises(KeyError):
            calculate_periodic_interest_rate(0.12, "yearly")


class TestAdjustPaymentDate(TestCase):
    def test_adjust_payment_date_non_holiday(self):
        self.assertEqual(
            adjust_payment_date(pd.Timestamp("2024-01-02")), pd.Timestamp("2024-01-02")
        )

    def test_adjust_payment_date_holiday(self):
        self.assertEqual(
            adjust_payment_date(pd.Timestamp("2024-01-01")), pd.Timestamp("2023-12-29")
        )  # New Year rolls back

    def test_adjust_payment_date_weekend(self):
        self.assertEqual(
            adjust_payment_date(pd.Timestamp("2024-01-06")), pd.Timestamp("2024-01-05")
        )  # Weekend rolls back to Friday

    def test_adjust_payment_date_labor_day(self):
        self.assertEqual(
            adjust_payment_date(pd.Timestamp("2024-05-01")), pd.Timestamp("2024-04-30")
        )

    def test_adjust_payment_date_range_for_consistency(self):
        dates = pd.date_range(start="2024-01-01", periods=10, freq="B")
        adjusted_dates = [adjust_payment_date(date) for date in dates]
        for adjusted_date in adjusted_dates:
            self.assertNotIn(adjusted_date.weekday(), [5, 6])  # Not Saturday or Sunday


class TestAmortizationSchedule(TestCase):
    def test_generate_amortization_schedule_monthly_normal(self):
        df = generate_amortization_schedule(
            10000, 0.12, 12, "monthly", "2024-01-01", None
        )
        self.assertEqual(len(df), 13)  # 12 payments + initial entry
        self.assertAlmostEqual(df.iloc[-1]["Remaining Balance"], 0)

    def test_generate_amortization_schedule_biweekly_normal(self):
        df = generate_amortization_schedule(
            10000, 0.12, 26, "biweekly", "2024-01-01", None
        )
        self.assertEqual(len(df), 27)  # 26 payments + initial entry
        self.assertAlmostEqual(df.iloc[-1]["Remaining Balance"], 0)

    def test_generate_amortization_schedule_monthly_edge_case_leap_year(self):
        df = generate_amortization_schedule(
            10000, 0.12, 12, "monthly", "2024-02-29", None
        )
        self.assertTrue(df["Payment Date"].str.contains("2024-02-29").any())

    def test_generate_amortization_schedule_bimonthly_payment_due_day_adjustment(self):
        df = generate_amortization_schedule(
            10000, 0.12, 6, "bimonthly", "2024-01-30", 32
        )
        self.assertTrue(df["Payment Date"].str.contains("2024-03-29").any())
        # March 29th is the closest business day

    def test_generate_amortization_schedule_quarterly_end_of_month_handling(self):
        df = generate_amortization_schedule(
            10000, 0.12, 4, "quarterly", "2024-01-31", 31
        )
        # Ensures that payment due day is adjusted for months with less than 31 days
        self.assertTrue(
            df["Payment Date"].str.contains("2024-04-30").any()
        )  # April has 30 days

    def test_generate_amortization_schedule_zero_subline_amount(self):
        df = generate_amortization_schedule(0, 0.12, 12, "monthly", "2024-01-01", None)
        self.assertTrue(all(df["Remaining Balance"] == 0))

    def test_generate_amortization_schedule_negative_subline_amount(self):
        df = generate_amortization_schedule(
            -10000, 0.12, 12, "monthly", "2024-01-01", None
        )
        self.assertTrue(all(df["Remaining Balance"] <= 0))

    def test_generate_amortization_schedule_varied_start_dates(self):
        start_dates = ["2024-01-01", "2024-06-15", "2024-12-31"]
        for start_date in start_dates:
            df = generate_amortization_schedule(
                10000, 0.12, 12, "monthly", start_date, None
            )
            self.assertEqual(len(df), 13)
            self.assertAlmostEqual(df.iloc[-1]["Remaining Balance"], 0)


class TestSpecialDateAdjustments(TestCase):
    def test_adjust_payment_date_end_of_month(self):
        self.assertEqual(
            adjust_payment_date(pd.Timestamp("2024-02-28")), pd.Timestamp("2024-02-28")
        )

    def test_adjust_payment_date_leap_year(self):
        self.assertEqual(
            adjust_payment_date(pd.Timestamp("2024-02-29")), pd.Timestamp("2024-02-29")
        )


class TestInterestCalculationAccuracy(TestCase):
    def test_interest_calculation_for_high_rate(self):
        df = generate_amortization_schedule(
            10000, 0.24, 12, "monthly", "2024-01-01", None
        )
        expected_interest_first_payment = 10000 * (0.24 / 12)
        self.assertAlmostEqual(df.iloc[1]["Interest"], expected_interest_first_payment)

    def test_interest_calculation_over_long_term(self):
        df = generate_amortization_schedule(
            10000, 0.50, 120, "monthly", "2024-01-01", None
        )
        total_interest_paid = df["Interest"].sum()
        self.assertTrue(total_interest_paid > 0)


class TestPrincipalDeduction(TestCase):
    def test_principal_deduction_consistency(self):
        # Test that the principal is reducing consistently in accordance to payments
        df = generate_amortization_schedule(
            10000, 0.12, 12, "monthly", "2024-01-01", None
        )
        last_balance = 10000
        for index, row in df.iterrows():
            if index > 0:  # Skipping the initial entry
                self.assertTrue(last_balance >= row["Remaining Balance"])
                last_balance = row["Remaining Balance"]


class TestFinalPaymentAndBalance(TestCase):
    def test_final_balance_closure(self):
        # Ensure the final balance is zero, indicating the loan is fully paid off
        df = generate_amortization_schedule(
            10000, 0.12, 12, "monthly", "2024-01-01", None
        )
        self.assertAlmostEqual(df.iloc[-1]["Remaining Balance"], 0)

    def test_final_payment_amount_adjustment(self):
        # Test to ensure the last payment amount correctly closes out the loan
        df = generate_amortization_schedule(
            10000, 0.12, 5, "monthly", "2024-01-01", None
        )
        last_payment = df.iloc[-1]["Total Payment"]
        expected_last_payment = df.iloc[-2]["Remaining Balance"] * (1 + 12 / 12 / 100)
        self.assertAlmostEqual(last_payment, expected_last_payment)
