from credit_origination.api.serializers import (
    CreditTypeAdminSerializer,
    CreditTypeSerializer,
)
from django.utils.dateparse import parse_datetime
from accounts.tests.base_test import BaseTest


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
