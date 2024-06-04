from django.test import TestCase
from accounts.api.serializers import (
    UserSerializer,
    UserSerializerWithToken,
    RegisterRequestSerializer,
    ForgotPasswordSerializer,
    PasswordResetConfirmSerializer,
)
from accounts.tests.base_test import BaseTest
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

    def test_read_only_fields(self):
        read_only_data = {
            "id": 999,
            "username": "new_username",
            "created": "2024-01-01T00:00:00Z",
            "is_active": False,
            "is_staff": True,
            "is_superuser": True,
        }
        serializer = UserSerializer(
            instance=self.user, data=read_only_data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data

        # Check that read-only fields are not in validated_data
        for field_name in UserSerializer.Meta.read_only_fields:
            self.assertNotIn(field_name, validated_data)

    def test_update_non_read_only_fields(self):
        update_data = {
            "first_name": "James",
            "last_name": "Hendrix",
            "second_last_name": "Marshall",
            "email": "james@hendrix.com",
        }
        serializer = UserSerializer(instance=self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()

        for field_name, value in update_data.items():
            self.assertEqual(getattr(self.user, field_name), value)

    def test_update_read_only_fields(self):
        update_data = {
            "username": "new_username",
            "created": "2024-01-01T00:00:00Z",
            "is_active": False,
            "is_staff": True,
            "is_superuser": True,
        }
        serializer = UserSerializer(instance=self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()

        # Check that read-only fields have not been updated
        read_only_fields = UserSerializer.Meta.read_only_fields
        for field_name in read_only_fields:
            if field_name in self.user_data:
                self.assertEqual(
                    getattr(self.user, field_name), self.user_data[field_name]
                )
            else:
                # For the 'id' field, check that it remains the same
                if field_name == "id":
                    self.assertEqual(getattr(self.user, field_name), self.user.id)


class UserSerializerWithTokenTest(UserSerializerTest):
    def test_token_field(self):
        serializer = UserSerializerWithToken(instance=self.user)
        # simply check if 'token' field exists
        self.assertIn("token", serializer.data)

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
        serializer = UserSerializerWithToken(instance=self.user)
        data = serializer.data
        # Check if data is correctly returned
        for field_name in self.user_data.keys():
            self.assertEqual(data[field_name], self.user_data[field_name])
        # Check if token is included
        self.assertIn("token", data)

    def test_invalid_serializer_data(self):
        # Testing without required fields
        invalid_data = self.user_data.copy()
        invalid_data["email"] = ""
        serializer = UserSerializerWithToken(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertTrue("email" in serializer.errors)

    def test_read_only_fields(self):
        read_only_data = {
            "id": 999,
            "username": "new_username",
            "created": "2024-01-01T00:00:00Z",
            "is_active": False,
            "is_staff": True,
            "is_superuser": True,
            "token": "fake_token",
        }
        serializer = UserSerializerWithToken(
            instance=self.user, data=read_only_data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        validated_data = serializer.validated_data

        # Check that read-only fields are not in validated_data
        for field_name in UserSerializerWithToken.Meta.read_only_fields:
            self.assertNotIn(field_name, validated_data)

    def test_update_non_read_only_fields(self):
        update_data = {
            "first_name": "James",
            "last_name": "Hendrix",
            "second_last_name": "Marshall",
            "email": "james@hendrix.com",
        }
        serializer = UserSerializerWithToken(
            instance=self.user, data=update_data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()

        for field_name, value in update_data.items():
            self.assertEqual(getattr(self.user, field_name), value)

    def test_update_read_only_fields(self):
        update_data = {
            "username": "new_username",
            "created": "2024-01-01T00:00:00Z",
            "is_active": False,
            "is_staff": True,
            "is_superuser": True,
            "token": "fake_token",
        }
        serializer = UserSerializerWithToken(
            instance=self.user, data=update_data, partial=True
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()

        # Check that read-only fields have not been updated
        read_only_fields = UserSerializerWithToken.Meta.read_only_fields
        for field_name in read_only_fields:
            if field_name in self.user_data:
                self.assertEqual(
                    getattr(self.user, field_name), self.user_data[field_name]
                )
            else:
                # For the 'id' field, check that it remains the same
                if field_name == "id":
                    self.assertEqual(getattr(self.user, field_name), self.user.id)
                elif field_name == "token":
                    # Check that token is present and of correct type
                    self.assertIn(field_name, serializer.data)
                    self.assertIsInstance(serializer.data[field_name], str)


class RegisterRequestSerializerTest(TestCase):
    def test_valid_serializer_data(self):
        # Ensure the password meets the custom validator requirements
        valid_data = {
            "first_name": "Brent",
            "last_name": "Mydland",
            "email": "brent@grateful.com",
            "password": "Valid$123",
        }
        serializer = RegisterRequestSerializer(data=valid_data)
        if not serializer.is_valid():
            print(serializer.errors)
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer_data(self):
        invalid_data = {
            "first_name": "",
            "last_name": "",
            "email": "notanemail",
            "password": "short",
        }
        serializer = RegisterRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("first_name", serializer.errors)
        self.assertIn("last_name", serializer.errors)
        self.assertIn("email", serializer.errors)
        self.assertIn("password", serializer.errors)


class ForgotPasswordSerializerTest(BaseTest):
    def test_valid_email(self):
        serializer = ForgotPasswordSerializer(data={"email": "phil@grateful.com"})
        # self.assertTrue(serializer.is_valid())
        valid = serializer.is_valid()
        self.assertTrue(valid, msg=f"Serializer errors: {serializer.errors}")

    def test_nonexistent_email(self):
        serializer = ForgotPasswordSerializer(data={"email": "nonexistent@example.com"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class PasswordResetConfirmSerializerTest(TestCase):
    def test_passwords_match_valid(self):
        valid_data = {
            "password": "Newsecurepassword@1",
            "confirm_password": "Newsecurepassword@1",
            # at least 8 chars, special symbol, capital letter, and digit.
        }
        serializer = PasswordResetConfirmSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

    def test_passwords_match_but_invalid(self):
        invalid_data = {
            "password": "Short1",
            "confirm_password": "Short1",
            # missing special symbol and min length is 8 chars
        }
        serializer = PasswordResetConfirmSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_passwords_do_not_match(self):
        invalid_data = {
            "password": "newpassword",
            "confirm_password": "different_password",
        }
        serializer = PasswordResetConfirmSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_password", serializer.errors)
