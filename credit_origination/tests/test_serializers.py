from credit_origination.api.serializers import (
    CreditTypeAdminSerializer,
    CreditTypeSerializer,
    CreditRequestSerializer,
    CreditRequestStatusUpdateSerializer,
)
from credit_origination.models import CreditRequest
from django.utils.dateparse import parse_datetime
from accounts.tests.base_test import BaseTest
from decimal import Decimal


class CreditTypeAdminSerializerTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.serializer = CreditTypeAdminSerializer(instance=self.credit_type)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertCountEqual(
            data.keys(), ["id", "name", "description", "active", "created"]
        )

    def test_read_only_fields(self):
        data = self.serializer.data
        self.assertTrue("id" in data and "created" in data)
        self.assertIsInstance(data["id"], int)
        self.assertIsInstance(data["created"], str)

    def test_valid_data(self):
        serializer = CreditTypeAdminSerializer(data=self.credit_type_data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_data(self):
        invalid_data = {
            "name": "",
            "description": "A loan for personal expenses",
            "active": True,
        }
        serializer = CreditTypeAdminSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(set(serializer.errors.keys()), set(["name"]))

    def test_update_credit_type(self):
        updated_data = {
            "name": "Updated Loan",
            "description": "Updated description",
            "active": False,
        }
        serializer = CreditTypeAdminSerializer(
            instance=self.credit_type, data=updated_data
        )
        self.assertTrue(serializer.is_valid())
        updated_credit_type = serializer.save()
        self.assertEqual(updated_credit_type.name, "Updated Loan")
        self.assertEqual(updated_credit_type.description, "Updated description")
        self.assertFalse(updated_credit_type.active)


class CreditTypeSerializerTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.serializer = CreditTypeSerializer(instance=self.credit_type)

    def test_contains_expected_fields(self):
        data = self.serializer.data
        self.assertCountEqual(data.keys(), ["id", "name", "description", "created"])

    def test_read_only_fields(self):
        data = self.serializer.data
        self.assertTrue(
            "id" in data
            and "created" in data
            and "name" in data
            and "description" in data
        )
        self.assertIsInstance(data["id"], int)
        self.assertIsInstance(data["created"], str)
        self.assertIsInstance(data["name"], str)
        self.assertIsInstance(data["description"], str)

    def test_read_only_values(self):
        data = self.serializer.data
        self.assertEqual(data["name"], self.credit_type_data["name"])
        self.assertEqual(data["description"], self.credit_type_data["description"])
        self.assertEqual(parse_datetime(data["created"]), self.credit_type.created)


class CreditRequestSerializerTest(BaseTest):
    def setUp(self):
        self.credit_request_data = {
            "credit_type": self.credit_type.id,
            "amount": Decimal("5000.00"),
            "term": 24,
            "user": self.user.id,
        }
        self.credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
        )

    def test_credit_request_serializer_valid_data(self):
        serializer = CreditRequestSerializer(data=self.credit_request_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["amount"], self.credit_request_data["amount"]
        )

    def test_credit_request_serializer_invalid_amount(self):
        invalid_data = self.credit_request_data.copy()
        invalid_data["amount"] = -1000
        serializer = CreditRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_credit_request_serializer_invalid_term(self):
        invalid_data = self.credit_request_data.copy()
        invalid_data["term"] = 150
        serializer = CreditRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("term", serializer.errors)

    def test_credit_request_serializer_read_only_fields(self):
        serializer = CreditRequestSerializer(self.credit_request)
        self.assertIn("id", serializer.data)
        self.assertIn("created", serializer.data)
        self.assertIn("status", serializer.data)
        self.assertEqual(serializer.data["status"], "pending")


class CreditRequestStatusUpdateSerializerTest(BaseTest):
    def setUp(self):
        self.credit_request = CreditRequest.objects.create(
            credit_type=self.credit_type,
            amount=Decimal("5000.00"),
            term=24,
            user=self.user,
        )

    def test_credit_request_status_update_serializer_valid_data(self):
        update_data = {"status": "approved"}
        serializer = CreditRequestStatusUpdateSerializer(
            self.credit_request, data=update_data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data["status"], "approved")

    def test_credit_request_status_update_serializer_invalid_status(self):
        update_data = {"status": "invalid_status"}
        serializer = CreditRequestStatusUpdateSerializer(
            self.credit_request, data=update_data, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_credit_request_status_update_serializer_read_only_fields(self):
        initial_data = {
            "credit_type": self.credit_request.credit_type,
            "amount": self.credit_request.amount,
            "term": self.credit_request.term,
            "created": self.credit_request.created,
            "user": self.credit_request.user,
        }
        update_data = {
            "credit_type": None,
            "amount": 10000,
            "term": 36,
            "status": "approved",
        }
        serializer = CreditRequestStatusUpdateSerializer(
            self.credit_request, data=update_data, partial=True
        )
        self.assertTrue(serializer.is_valid())

        # Ensure read-only fields are unchanged
        for field, value in initial_data.items():
            self.assertEqual(getattr(self.credit_request, field), value)
