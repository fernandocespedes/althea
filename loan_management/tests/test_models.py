from credit_subline.tests.base_test import BaseCreditSublineViewTests
from credit_subline.models import CreditSubline
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from loan_management.models import LoanTerm
from django.utils import timezone


class LoanTermModelTests(BaseCreditSublineViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_subline = CreditSubline.objects.create(
            credit_line=cls.credit_line,
            subline_type=cls.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="pending",
        )

    def test_create_loan_term_with_valid_data(self):
        loan_term = LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
            status="approved",
        )
        self.assertEqual(loan_term.term_length, 12)
        self.assertEqual(loan_term.repayment_frequency, "monthly")
        self.assertEqual(loan_term.payment_due_day, 15)
        self.assertEqual(loan_term.status, "approved")

    def test_invalid_repayment_frequency(self):
        loan_term = LoanTerm(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="yearly",  # Invalid choice
            payment_due_day=10,
            start_date=timezone.now().date(),
        )
        with self.assertRaises(ValidationError):
            loan_term.full_clean()

    def test_payment_due_day_greater_than_31(self):
        with self.assertRaises(ValidationError):
            loan_term = LoanTerm(
                credit_subline=self.credit_subline,
                term_length=12,
                repayment_frequency="monthly",
                payment_due_day=32,
                start_date=timezone.now().date(),
            )
            loan_term.full_clean()

    def test_str_representation(self):
        loan_term = LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
        )
        expected_str = (
            f"Loan Term for {loan_term.credit_subline} on "
            f"{loan_term.created.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        self.assertEqual(str(loan_term), expected_str)

    def test_default_ordering(self):
        credit_subline_2 = CreditSubline.objects.create(
            credit_line=self.credit_line,
            subline_type=self.credit_type,
            subline_amount=500000,
            interest_rate=5.5,
            status="pending",
        )
        loan_term_1 = LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date() - timezone.timedelta(days=1),
        )

        loan_term_2 = LoanTerm.objects.create(
            credit_subline=credit_subline_2,
            term_length=24,
            repayment_frequency="biweekly",
            payment_due_day=1,
            start_date=timezone.now().date(),
        )

        first_loan_term = LoanTerm.objects.first()
        self.assertEqual(
            first_loan_term,
            loan_term_2,
            "Loan terms are not ordered by start_date in descending order",
        )
        self.assertTrue(loan_term_1 in LoanTerm.objects.all())

    def test_cannot_create_second_loanterm_for_same_credit_subline(self):
        LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
        )

        # Attempt to create a second LoanTerm instance with the same CreditSubline
        with self.assertRaises(IntegrityError):
            LoanTerm.objects.create(
                credit_subline=self.credit_subline,
                term_length=24,
                repayment_frequency="biweekly",
                payment_due_day=1,
                start_date=timezone.now().date(),
            )

    def test_loan_term_status_field_choices(self):
        # Valid status
        loan_term = LoanTerm(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
            status="rejected",  # Valid choice
        )
        loan_term.full_clean()

        # Invalid status
        loan_term.status = "invalid_status"
        with self.assertRaises(ValidationError):
            loan_term.full_clean()

    def test_default_status(self):
        loan_term = LoanTerm.objects.create(
            credit_subline=self.credit_subline,
            term_length=12,
            repayment_frequency="monthly",
            payment_due_day=15,
            start_date=timezone.now().date(),
        )
        self.assertEqual(
            loan_term.status, "pending", "Default status should be 'pending'"
        )
