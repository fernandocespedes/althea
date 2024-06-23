from accounts.tests.base_test import BaseTest
from credit_line.models import CreditLine
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse


class BaseCreditSublineViewTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.credit_line = CreditLine.objects.create(
            credit_limit=Decimal("1000000"),
            currency="mxn",
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=365),
            status="approved",
            user=cls.user,
        )

        cls.create_url = reverse(
            "credit_subline_api:credit_subline_create",
            kwargs={"credit_line_pk": cls.credit_line.pk},
        )

        cls.data = {
            "subline_type": cls.credit_type.pk,
            "subline_amount": Decimal("1000.00"),
            "amount_disbursed": Decimal("0.00"),
            "outstanding_balance": Decimal("0.00"),
            "interest_rate": Decimal("0.05"),
            "status": "pending",
        }

        cls.admin_list_url = reverse("credit_subline_api:credit_sublines_admin_list")
