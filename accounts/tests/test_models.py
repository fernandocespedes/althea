from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            first_name="Jerry",
            last_name="Garcia",
            username="gratefuljerry",
            email="jerry@grateful.com",
            password="password123",
        )
        cls.superuser = User.objects.create_superuser(
            first_name="Bob",
            last_name="Weir",
            username="bobbyweir",
            email="bobby@grateful.com",
            password="admin123",
        )

    def test_full_name(self):
        user = User.objects.get(username="gratefuljerry")
        self.assertEqual(user.full_name(), "Jerry Garcia")

    def test_create_user(self):
        user = User.objects.get(username="gratefuljerry")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.get(username="bobbyweir")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                first_name="Mark",
                last_name="Knopfler",
                username="diremark",
                password="password123",
                email="",  # empty email
            )

    def test_user_without_username_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                first_name="keith",
                last_name="richards",
                email="keith@rolling.com",
                password="password123",
                username="",  # empty 'username'
            )

    def test_email_field_unique(self):
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                first_name="mick",
                last_name="jagger",
                username="mickjagger",
                email="jerry@grateful.com",  # Duplicate email
                password="password123",
            )

    def test_default_values(self):
        user = User.objects.get(username="gratefuljerry")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)

    def test_update_user(self):
        user = User.objects.get(username="gratefuljerry")
        user.phone_number = "1234567890"
        user.save()
        updated_user = User.objects.get(username="gratefuljerry")
        self.assertEqual(updated_user.phone_number, "1234567890")

    def test_delete_user(self):
        user = User.objects.get(username="gratefuljerry")
        user.delete()
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username="gratefuljerry")
