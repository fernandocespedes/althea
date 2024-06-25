from django.db import models
from django.core.exceptions import ValidationError
from credit_line.models import CreditLine
from credit_origination.models import CreditType
from decimal import Decimal
from credit_line.models import current_date
from credit_subline.utils import interest_rate_by_100


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


class CreditAmountAdjustment(models.Model):
    ADJUSTMENT_STATUS_CHOICES = (
        ("pending_review", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("implemented", "Implemented"),
    )
    credit_subline = models.ForeignKey(
        CreditSubline, related_name="amount_adjustments", on_delete=models.CASCADE
    )
    initial_amount = models.DecimalField(max_digits=12, decimal_places=2)
    adjusted_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    effective_date = models.DateField(default=current_date)
    reason_for_adjustment = models.TextField()
    adjustment_status = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_STATUS_CHOICES,
        default="pending_review",
    )

    def clean(self):
        # Validate new amount
        if self.adjusted_amount and self.adjusted_amount <= 0:
            raise ValidationError({"adjusted_amount": "Amount must be greater than 0."})

        # Ensure the new credit subline amount does not exceed max_digits
        if len(str(self.adjusted_amount).replace(".", "").replace("-", "")) > 12:
            raise ValidationError(
                {"adjusted_amount": "Amount must not exceed 12 digits."}
            )

    def save(self, *args, **kwargs):
        if not self.pk:
            # If this is a new adjustment and not an update
            # Automatically set the initial amount from the associated CreditSubline
            self.initial_amount = self.credit_subline.subline_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Adjustment for {self.credit_subline} on {self.effective_date}"

    class Meta:
        ordering = ["-effective_date"]


class InterestRateAdjustment(models.Model):
    ADJUSTMENT_STATUS_CHOICES = (
        ("pending_review", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("implemented", "Implemented"),
    )
    credit_subline = models.ForeignKey(
        CreditSubline,
        related_name="interest_rate_adjustments",
        on_delete=models.CASCADE,
    )
    initial_interest_rate = models.DecimalField(max_digits=6, decimal_places=3)
    adjusted_interest_rate = models.DecimalField(max_digits=6, decimal_places=3)
    effective_date = models.DateField(default=current_date)
    reason_for_adjustment = models.TextField()
    adjustment_status = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_STATUS_CHOICES,
        default="pending_review",
    )

    def clean(self):
        if self.adjusted_interest_rate < 0:
            raise ValidationError(
                {"adjusted_interest_rate": "Interest rate cannot be negative."}
            )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.initial_interest_rate = interest_rate_by_100(
                self.credit_subline.interest_rate
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Interest Rate Adjustment for {self.credit_subline} on {self.effective_date}"

    class Meta:
        ordering = ["-effective_date"]


class CreditSublineStatusAdjustment(models.Model):
    ADJUSTMENT_STATUS_CHOICES = (
        ("pending_review", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("implemented", "Implemented"),
    )
    credit_subline = models.ForeignKey(
        CreditSubline,
        related_name="subline_status_adjustments",
        on_delete=models.CASCADE,
    )
    initial_status = models.CharField(
        max_length=25,
        choices=CreditSubline.SUBLINE_STATUS,
    )
    adjusted_status = models.CharField(
        max_length=25,
        choices=CreditSubline.SUBLINE_STATUS,
    )
    effective_date = models.DateField(default=current_date)
    reason_for_adjustment = models.TextField()
    adjustment_status = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_STATUS_CHOICES,
        default="pending_review",
    )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.initial_status = self.credit_subline.status

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Subline Status Adjustment for {self.credit_subline} on {self.effective_date}"

    class Meta:
        ordering = ["-effective_date"]
