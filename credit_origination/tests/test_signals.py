from django.utils import timezone
from credit_origination.models import CreditRequest
from credit_line.models import CreditLine
from accounts.tests.base_test import BaseTest


class CreditRequestSignalTestCase(BaseTest):

    def setUp(self):
        super().setUp()

    def test_previous_status_capture(self):
        """
        Ensure that the previous status is correctly captured before
        saving the CreditRequest.
        """
        credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=10000,
            term=12,
            status="pending",
        )
        credit_request.status = "approved"
        credit_request.save()
        self.assertEqual(credit_request._previous_status, "pending")

    def test_create_credit_line_on_approval(self):
        """
        Ensure that a CreditLine is created with the correct details
        when the CreditRequest status changes to 'approved'.
        """
        credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=10000,
            term=12,
            status="pending",
        )
        credit_request.status = "approved"
        credit_request.save()
        credit_line = CreditLine.objects.get(user=self.user)
        self.assertEqual(credit_line.credit_limit, credit_request.amount)
        self.assertEqual(credit_line.status, "pending")
        self.assertEqual(credit_line.currency, "mxn")
        self.assertEqual(credit_line.start_date, timezone.now().date())

    def test_no_credit_line_on_non_approval(self):
        """
        Check that no CreditLine is created if the CreditRequest
        tatus changes to something other than 'approved'.
        """
        credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=10000,
            term=12,
            status="pending",
        )
        credit_request.status = "rejected"
        credit_request.save()
        with self.assertRaises(CreditLine.DoesNotExist):
            CreditLine.objects.get(user=self.user)

    def test_no_duplicate_credit_line_on_reapproval(self):
        """
        Ensure that no duplicate CreditLine is created if the CreditRequest
        status is set to 'approved' again after being 'approved' initially.
        """
        credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=10000,
            term=12,
            status="pending",
        )
        credit_request.status = "approved"
        credit_request.save()
        credit_line = CreditLine.objects.get(user=self.user)
        self.assertEqual(credit_line.credit_limit, credit_request.amount)
        self.assertEqual(CreditLine.objects.filter(user=self.user).count(), 1)

        credit_request.status = "approved"
        credit_request.save()
        self.assertEqual(CreditLine.objects.filter(user=self.user).count(), 1)

    def test_credit_line_not_created_if_already_approved(self):
        """
        Confirm that a CreditLine is not created if the CreditRequest was already
        'approved' at creation time, and only creates it when it transitions to 'approved'.
        """
        credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=10000,
            term=12,
            status="approved",
        )
        self.assertEqual(CreditLine.objects.filter(user=self.user).count(), 0)

        credit_request.status = "pending"
        credit_request.save()

        credit_request.status = "approved"
        credit_request.save()
        self.assertEqual(CreditLine.objects.filter(user=self.user).count(), 1)

    def test_credit_line_retains_original_limit_on_new_credit_request(self):
        """
        Create a credit request, approve it, so a credit line is created,
        then create another credit request with a different amount,
        and verify that the credit limit remains the one established
        when the credit line was created.
        """
        first_credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=10000,
            term=12,
            status="pending",
        )
        first_credit_request.status = "approved"
        first_credit_request.save()

        # Verify the credit line created with the first credit request
        credit_line = CreditLine.objects.get(user=self.user)
        self.assertEqual(credit_line.credit_limit, first_credit_request.amount)

        second_credit_request = CreditRequest.objects.create(
            user=self.user,
            credit_type=self.credit_type,
            amount=20000,
            term=24,
            status="pending",
        )
        second_credit_request.status = "approved"
        second_credit_request.save()

        # Verify the credit line still has the original credit limit
        credit_line.refresh_from_db()
        self.assertEqual(credit_line.credit_limit, 10000)
