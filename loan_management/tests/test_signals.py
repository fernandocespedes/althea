from credit_subline.tests.base_test import BaseCreditSublineViewTests
from credit_subline.models import CreditSubline
from decimal import Decimal
from django.utils import timezone
from loan_management.models import LoanTerm, PeriodicPayment
from loan_management.signals import (
    generate_periodic_payments,
    _previous_loan_term_status,
    capture_previous_loan_term_status,
)


class GeneratePeriodicPaymentsSignalTests(BaseCreditSublineViewTests):
    def setUp(self):
        super().setUp()

        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_amount=Decimal("50000"),
            interest_rate=Decimal("5.0"),
            status="pending",
        )

        self.loan_term = LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="biweekly",
            payment_due_day=15,
            start_date=timezone.now().date(),
            status="pending",
        )

        self.expected_number_of_payments = self.loan_term.term_length + 1

    def test_generate_periodic_payments_signal_no_action(self):
        generate_periodic_payments(
            sender=LoanTerm, instance=self.loan_term, created=False
        )
        self.assertEqual(PeriodicPayment.objects.count(), 0)

    def test_generate_periodic_payments_signal_approved(self):
        # Change LoanTerm status to approved
        self.loan_term.status = "approved"
        self.loan_term.save()

        # Check if PeriodicPayment instances are created
        self.assertEqual(
            PeriodicPayment.objects.count(), self.expected_number_of_payments
        )

    def test_generate_periodic_payments_signal_rejected(self):
        # Change LoanTerm status to rejected
        self.loan_term.status = "rejected"
        self.loan_term.save()

        # Trigger the signal
        generate_periodic_payments(
            sender=LoanTerm, instance=self.loan_term, created=False
        )

        # Ensure no PeriodicPayment instances are created
        self.assertEqual(PeriodicPayment.objects.count(), 0)

    def test_generate_periodic_payments_signal_pending_to_approved(self):
        # Ensure no PeriodicPayment instances are created initially
        self.assertEqual(PeriodicPayment.objects.count(), 0)

        # Change LoanTerm status from pending to approved
        self.loan_term.status = "approved"
        self.loan_term.save()

        # The signal is triggered dynamically
        # Check if PeriodicPayment instances are created
        self.assertEqual(
            PeriodicPayment.objects.count(), self.expected_number_of_payments
        )

    def test_generate_periodic_payments_signal_no_instance(self):
        generate_periodic_payments(sender=LoanTerm, instance=None, created=False)
        self.assertEqual(PeriodicPayment.objects.count(), 0)

    def test_generate_periodic_payments_signal_approved_idempotency(self):
        # Change LoanTerm status to approved
        self.loan_term.status = "approved"
        self.loan_term.save()

        # Check if PeriodicPayment instances are created
        self.assertEqual(
            PeriodicPayment.objects.count(), self.expected_number_of_payments
        )

        self.loan_term.status = "approved"
        self.loan_term.save()

        # Instances shouldn't be duplicated
        self.assertEqual(
            PeriodicPayment.objects.count(), self.expected_number_of_payments
        )


class CapturePreviousLoanTermStatusSignalTests(BaseCreditSublineViewTests):
    def setUp(self):
        super().setUp()
        # Create a CreditSubline instance
        self.credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_amount=Decimal("50000"),
            interest_rate=Decimal("5.0"),
            status="pending",
        )

        # Create LoanTerm instance
        self.loan_term = LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
            status="pending",
        )

    def test_capture_previous_loan_term_status(self):
        # Change LoanTerm status to approved
        self.loan_term.status = "approved"
        self.loan_term.save()

        # Check if previous status is captured correctly
        self.assertEqual(_previous_loan_term_status[self.loan_term.pk], "pending")

    def test_capture_previous_loan_term_status_no_instance(self):
        # Check if no instance is created if no LoanTerm instance is provided
        _previous_loan_term_status.clear()
        capture_previous_loan_term_status(sender=LoanTerm, instance=None)
        self.assertEqual(len(_previous_loan_term_status), 0)

    def test_capture_previous_loan_term_status_created(self):
        # Create a new CreditSubline instance
        new_credit_subline = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_amount=Decimal("75000"),
            interest_rate=Decimal("6.0"),
            status="active",
        )

        # Create a new LoanTerm instance
        new_loan_term = LoanTerm.objects.create(
            credit_subline=new_credit_subline,
            term_length=6,
            repayment_frequency="biweekly",
            payment_due_day=10,
            start_date=timezone.now().date(),
            status="rejected",
        )

        # Check if no previous status is captured for a newly created instance
        self.assertNotIn(new_loan_term.pk, _previous_loan_term_status)
