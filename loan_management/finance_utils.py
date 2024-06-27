import pandas as pd
from pandas.tseries.holiday import AbstractHolidayCalendar, nearest_workday, Holiday
from pandas.tseries.offsets import CustomBusinessDay
from pandas import Timestamp
import numpy_financial as npf


class MexicanHolidaysCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday("New Year", month=1, day=1, observance=nearest_workday),
        Holiday("Constitution Day", month=2, day=5, observance=nearest_workday),
        Holiday("Benito Juarez Birthday", month=3, day=21, observance=nearest_workday),
        Holiday("Labor Day", month=5, day=1, observance=nearest_workday),
        Holiday("Independence Day", month=9, day=16, observance=nearest_workday),
        Holiday("Revolution Day", month=11, day=20, observance=nearest_workday),
        Holiday("Christmas", month=12, day=25, observance=nearest_workday),
    ]


mex_bday = CustomBusinessDay(calendar=MexicanHolidaysCalendar())


def adjust_payment_date(date):
    """Adjust the payment date to the previous
    valid business day if it falls on a holiday or weekend."""
    return mex_bday.rollback(date)


def calculate_periodic_interest_rate(annual_rate, frequency):
    """Calculate the periodic interest rate based on the repayment frequency.
    Assumes annual_rate is a decimal."""
    frequency_map = {
        "monthly": 12,
        "biweekly": 26,  # Approximately 26 biweekly periods in a year
        "bimonthly": 6,  # Once every two months
        "quarterly": 4,  # Once every three months
    }
    if not (0 <= annual_rate <= 1):  # Validate that the rate is a reasonable decimal
        raise ValueError(
            "Annual interest rate should be between 0 and 1 (e.g., 0.05 for 5%)"
        )
    return annual_rate / frequency_map[frequency]


def generate_amortization_schedule(
    subline_amount,
    interest_rate,
    term_length,
    repayment_frequency,
    start_date_str,
    payment_due_day,
):
    """Generate an amortization schedule with specified parameters."""
    period_interest_rate = calculate_periodic_interest_rate(
        interest_rate, repayment_frequency
    )
    start_date = pd.to_datetime(start_date_str)
    current_date = start_date

    # Calculate the periodic payment amount
    periodic_payment = npf.pmt(period_interest_rate, term_length, -subline_amount)
    current_balance = subline_amount

    # Initial entry
    records = [
        {
            "Payment Date": start_date.strftime("%Y-%m-%d"),
            "Principal": 0,
            "Interest": 0,
            "Total Payment": 0,
            "Remaining Balance": subline_amount,
        }
    ]

    if repayment_frequency == "biweekly":
        # Generate biweekly payment dates
        dates = [start_date]
        for _ in range(term_length):
            current_date += pd.DateOffset(weeks=2)
            if current_date > Timestamp.max - pd.DateOffset(
                weeks=2
            ):  # Prevent overflow
                break  # Or handle the case as needed
            dates.append(adjust_payment_date(current_date))

        for payment_date in dates[1:]:
            # Calculate interest for the period
            interest = current_balance * period_interest_rate
            principal = periodic_payment - interest
            if principal > current_balance:
                principal = current_balance

            current_balance -= principal

            # If the remaining balance is sufficiently close to zero, round down to zero.
            if abs(current_balance) < 0.01:  # Assuming currency rounding to cents
                current_balance = 0

            records.append(
                {
                    "Payment Date": payment_date.strftime("%Y-%m-%d"),
                    "Principal": principal,
                    "Interest": interest,
                    "Total Payment": principal + interest,
                    "Remaining Balance": current_balance,
                }
            )

            # Stop processing if the balance is zero
            if current_balance <= 0:
                break

    else:
        # Handle monthly, bimonthly, and quarterly payments
        offsets = {
            "monthly": pd.DateOffset(months=1),
            "bimonthly": pd.DateOffset(months=2),
            "quarterly": pd.DateOffset(months=3),
        }
        date_offset = offsets[repayment_frequency]

        while current_balance > 0:
            current_date += date_offset
            if current_date > Timestamp.max - date_offset:  # Prevent overflow
                break  # Or handle the case as needed

            if payment_due_day:
                # Find the last valid day of the month if
                # payment_due_day exceeds the number of days in the month
                current_date = current_date.replace(
                    day=min(
                        payment_due_day,
                        pd.Timestamp(
                            current_date.year, current_date.month, 1
                        ).days_in_month,
                    )
                )

            current_date = adjust_payment_date(current_date)

            # Calculate interest for the period
            interest = current_balance * period_interest_rate
            principal = periodic_payment - interest
            if principal > current_balance:
                principal = current_balance

            current_balance -= principal

            # If the remaining balance is sufficiently close to zero, round down to zero.
            if abs(current_balance) < 0.01:  # Assuming currency rounding to cents
                current_balance = 0

            records.append(
                {
                    "Payment Date": current_date.strftime("%Y-%m-%d"),
                    "Principal": principal,
                    "Interest": interest,
                    "Total Payment": principal + interest,
                    "Remaining Balance": current_balance,
                }
            )

            # Stop processing if the balance is zero
            if current_balance <= 0:
                break

    amortization_schedule_df = pd.DataFrame(records)
    amortization_schedule_df = amortization_schedule_df.round(2)
    pd.options.display.float_format = "{:,.2f}".format

    return amortization_schedule_df
