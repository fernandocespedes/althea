from django.test import TestCase
from accounts.api.serializers import (
    UserSerializer,
    UserSerializerWithToken,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializerTest(TestCase):
    def setUp(self):
        self.user_data = {
            "first_name": "Jimmy",
            "last_name": "Hendrix",
            "second_last_name": "",
            "email": "jimmy@hendrix.com",
            "username": "jimmy_hendrix",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }
        self.user = User.objects.create(**self.user_data)

    def test_valid_serializer_data(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        # Check if data is correctly returned
        for field_name in self.user_data.keys():
            self.assertEqual(data[field_name], self.user_data[field_name])

    def test_invalid_serializer_data(self):
        # Testing without required fields
        invalid_data = self.user_data.copy()
        invalid_data["email"] = ""
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("email" in serializer.errors)


class UserSerializerWithTokenTest(UserSerializerTest):
    def test_token_field(self):
        serializer = UserSerializerWithToken(instance=self.user)
        # simply check if 'token' field exists
        self.assertIn("token", serializer.data)
