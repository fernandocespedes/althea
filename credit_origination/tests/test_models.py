from accounts.tests.base_test import BaseTest
from credit_origination.models import CreditType, CreditRequest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class CreditTypeModelTest(TestCase):

    def setUp(self):
        self.credit_type = CreditType.objects.create(
            name="Personal Loan", description="A loan for personal use", active=True
        )

    def test_credit_type_creation(self):
        self.assertEqual(self.credit_type.name, "Personal Loan")
        self.assertEqual(self.credit_type.description, "A loan for personal use")
        self.assertTrue(self.credit_type.active)
        self.assertIsNotNone(self.credit_type.created)

    def test_credit_type_str(self):
        self.assertEqual(str(self.credit_type), "Personal Loan")

    def test_credit_type_ordering(self):
        credit_type2 = CreditType.objects.create(
            name="Business Loan", description="A loan for business use", active=True
        )
        credit_types = CreditType.objects.all()
        self.assertEqual(credit_types[0], credit_type2)
        self.assertEqual(credit_types[1], self.credit_type)


class CreditRequestModelTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.credit_type = CreditType.objects.create(
            name="Personal Loan", description="A loan for personal use", active=True
        )

    def test_credit_request_amount_validation(self):
        invalid_credit_request = CreditRequest(
            credit_type=self.credit_type,
            amount=-500.00,
            term=12,
            user=self.user,
            status="pending",
        )
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("amount", context.exception.message_dict)

        invalid_credit_request.amount = 0.00
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("amount", context.exception.message_dict)

        invalid_credit_request.amount = 123456789012.34
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("amount", context.exception.message_dict)

    def test_credit_request_term_validation(self):
        invalid_credit_request = CreditRequest(
            credit_type=self.credit_type,
            amount=1000.00,
            term=-1,
            user=self.user,
            status="pending",
        )
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("term", context.exception.message_dict)

        invalid_credit_request.term = 0
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("term", context.exception.message_dict)

        invalid_credit_request.term = 121
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("term", context.exception.message_dict)

    def test_credit_request_creation(self):
        valid_credit_request = CreditRequest(
            credit_type=self.credit_type,
            amount=1000.00,
            term=12,
            user=self.user,
            status="pending",
        )
        try:
            valid_credit_request.full_clean()
            valid_credit_request.save()
        except ValidationError:
            self.fail("Valid credit request raised ValidationError unexpectedly!")

    def test_credit_request_default_status(self):
        credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=1000.00,
            term=12,
            user=self.user,
        )
        self.assertEqual(credit_request.status, "pending")

    def test_credit_request_status_choices(self):
        credit_request = CreditRequest(
            credit_type=self.credit_type,
            amount=1000.00,
            term=12,
            user=self.user,
        )
        invalid_status = "not_a_status"
        credit_request.status = invalid_status
        with self.assertRaises(ValidationError) as context:
            credit_request.full_clean()
        self.assertIn("status", context.exception.message_dict)

    def test_credit_request_null_credit_type(self):
        credit_request = CreditRequest(
            credit_type=None,
            amount=1000.00,
            term=12,
            user=self.user,
            status="pending",
        )
        try:
            credit_request.full_clean()
            credit_request.save()
        except ValidationError:
            self.fail(
                "Credit request with null credit_type raised ValidationError unexpectedly!"
            )

    def test_credit_request_user_fk_constraint(self):
        invalid_credit_request = CreditRequest(
            credit_type=self.credit_type,
            amount=1000.00,
            term=12,
            user=None,
            status="pending",
        )
        with self.assertRaises(ValidationError) as context:
            invalid_credit_request.full_clean()
        self.assertIn("user", context.exception.message_dict)

    def test_credit_request_string_representation(self):
        credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=1000.00,
            term=12,
            user=self.user,
            status="pending",
        )
        self.assertEqual(
            str(credit_request),
            f"{credit_request.user} - {credit_request.created} - {credit_request.status}",
        )

    def test_credit_request_ordering(self):
        credit_request1 = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=1000.00,
            term=12,
            user=self.user,
            status="pending",
        )
        credit_request2 = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=2000.00,
            term=24,
            user=self.user,
            status="approved",
        )
        credit_requests = CreditRequest.objects.all()
        self.assertEqual(credit_requests[0], credit_request2)
        self.assertEqual(credit_requests[1], credit_request1)
