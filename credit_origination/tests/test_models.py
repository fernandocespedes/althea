from credit_origination.models import CreditType
from django.test import TestCase
from django.contrib.auth import get_user_model

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
