from django.test import TestCase, RequestFactory
from accounts.api.utils import (
    send_user_email,
    generate_username,
    custom_password_validator,
)
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError

User = get_user_model()


class UtilsTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            first_name="David",
            last_name="Smith",
            email="david@example.com",
            username="davidsmith",
            password="password123",
        )

    def test_send_user_email(self):
        # Create a mock request using RequestFactory
        request = self.factory.get(
            "/fake-url"
        )  # The URL doesn't matter in this context

        # Use the mock request in your function call
        send_user_email(
            request,
            self.user,
            "Subject",
            "accounts/emails/account_verification_email.html",
        )

        # Assert that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Subject")


class UsernameGenerationTest(TestCase):
    def setUp(self):
        # Create users with all necessary fields
        User.objects.create_user(
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            username="testuser",
            password="password",
        )
        User.objects.create_user(
            first_name="Test1",
            last_name="User1",
            email="testuser1@example.com",
            username="testuser1",
            password="password1",
        )
        User.objects.create_user(
            first_name="Test2",
            last_name="User2",
            email="testuser2@example.com",
            username="testuser2",
            password="password2",
        )

    def test_unique_email(self):
        # Test with a unique email address
        email = "unique@example.com"
        username = generate_username(email, "Unique", "User")
        self.assertEqual(username, "unique")

    def test_duplicate_email_username(self):
        # Test with an email that would generate a duplicate username
        email = "testuser@gmail.com"
        username = generate_username(email, "Test", "User")
        self.assertNotEqual(username, "testuser")  # Should not be 'testuser'

    def test_append_sequence_for_uniqueness(self):
        # Test that a sequence number is appended for uniqueness
        email = "testuser@gmail.com"  # This will conflict with "testuser"
        username = generate_username(email, "Test", "User")
        # Expecting something like 'testuser3'
        self.assertTrue(username != "testuser" and username.startswith("testuser"))

    def test_multiple_sequence_appends(self):
        # This should trigger the generation of a username with an appended sequence number
        email = "testuser@anotherdomain.com"
        username = generate_username(email, "Test", "User")
        # The expected username should be 'testuser3',
        # assuming 'testuser', 'testuser1', and 'testuser2' are already taken
        expected_username = "testuser3"
        self.assertEqual(username, expected_username)


class CustomPasswordValidatorTest(TestCase):
    def test_password_with_all_requirements(self):
        # This password meets all the requirements
        valid_password = "Valid$123"
        try:
            custom_password_validator(valid_password)
        except ValidationError:
            self.fail("custom_password_validator raised ValidationError unexpectedly!")

    def test_password_without_digit(self):
        # This password lacks a digit
        with self.assertRaises(ValidationError):
            custom_password_validator("Invalid$Password")

    def test_password_without_uppercase(self):
        # This password lacks an uppercase letter
        with self.assertRaises(ValidationError):
            custom_password_validator("invalid$123")

    def test_password_without_special_character(self):
        # This password lacks a special character
        with self.assertRaises(ValidationError):
            custom_password_validator("Invalid123")
