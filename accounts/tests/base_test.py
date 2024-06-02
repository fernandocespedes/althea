from django.test import TestCase
from django.contrib.auth import get_user_model


User = get_user_model()


class BaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a User
        cls.user = User.objects.create_user(
            first_name="Phil",
            last_name="Lesh",
            email="phil@grateful.com",
            username="phil_lesh",
            password="password123",
        )
        cls.user.is_active = True
        cls.user.save()
