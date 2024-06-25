from credit_origination.models import CreditType
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

        cls.inactive_user = User.objects.create_user(
            first_name="Jerry",
            last_name="Garcia",
            username="Sherry",
            email="jerry@example.com",
            password="Password123@",
        )
        cls.inactive_user.is_active = False
        cls.inactive_user.save()

        cls.admin_user = User.objects.create_user(
            first_name="Bob",
            last_name="Weir",
            username="Bobby",
            email="bobby@example.com",
            password="Password123@",
        )
        cls.admin_user.is_active = True
        cls.admin_user.is_staff = True
        cls.admin_user.save()

        cls.superuser = User.objects.create_superuser(
            first_name="David",
            last_name="Gilmour",
            username="dave_gilmour",
            email="david@pfloyd.com",
            password="SomeValidP@ss88",
        )

        cls.regular_user = User.objects.create_user(
            first_name="Jeff",
            last_name="Chimenti",
            email="jeff@example.com",
            username="chimentikeyboards",
            password="Password123@",
        )
        cls.regular_user.is_active = True
        cls.regular_user.save()

        cls.credit_type_data = {
            "name": "Personal Loan",
            "description": "A loan for personal expenses",
            "active": True,
        }
        cls.credit_type = CreditType.objects.create(**cls.credit_type_data)
