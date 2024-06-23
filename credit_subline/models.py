from django.db import models
from django.core.exceptions import ValidationError
from credit_line.models import CreditLine
from credit_origination.models import CreditType
from decimal import Decimal


class CreditSubline(models.Model):
    SUBLINE_STATUS = (
        ("pending", "Pending"),
        ("active", "Active"),
        ("inactive", "Inactive"),
    )

    credit_line = models.ForeignKey(CreditLine, on_delete=models.CASCADE)
    subline_type = models.ForeignKey(
        CreditType, on_delete=models.SET_NULL, null=True, blank=True
    )
    subline_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_disbursed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    interest_rate = models.DecimalField(max_digits=6, decimal_places=3)
    status = models.CharField(max_length=25, choices=SUBLINE_STATUS, default="pending")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def clean(self):
        """Check if the CreditLine status is approved before
        allowing the CreditSubline status to be active.

        Ensure that interest rate is positive
        """
        if self.status == "active" and self.credit_line.status != "approved":
            raise ValidationError(
                "The CreditSubline can only be active if the CreditLine status is approved."
            )

        # ensure interest rate is positive
        if self.interest_rate and self.interest_rate < 0:
            raise ValidationError(
                {"interest_rate": "Interest rate cannot be negative."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call the clean method before saving
        if self.interest_rate and self.interest_rate > 1:
            self.interest_rate /= Decimal("100.0")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subline_type} - {self.subline_amount} - {self.status}"
