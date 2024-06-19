from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def current_date():
    return timezone.now().date()


class CreditLine(models.Model):
    CREDIT_LINE_STATUS = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    CURRENCY_OPTIONS = (
        ("mxn", "MXN"),
        # ("usd", "USD"),
    )
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, choices=CURRENCY_OPTIONS, default="mxn")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=25, choices=CREDIT_LINE_STATUS, default="pending"
    )
    created = models.DateTimeField(auto_now_add=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    def clean(self):
        # Custom validation for the credit limit
        if self.credit_limit and self.credit_limit <= 0:
            raise ValidationError(
                {"credit_limit": "Credit limit must be greater than 0."}
            )

        # Ensure the credit limit does not exceed max_digits
        if len(str(self.credit_limit).replace(".", "").replace("-", "")) > 12:
            raise ValidationError(
                {"credit_limit": "Credit limit must not exceed 12 digits."}
            )

        # Validate start_date and end_date if both are present
        if self.end_date and self.start_date >= self.end_date:
            raise ValidationError({"period": "Start date must be before the end date."})

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensures clean() is called before saving
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.credit_limit}"

    def make_adjustment(self, new_data, reason, update_only=False):
        if update_only:
            # Directly update the CreditLine attributes without creating a new adjustment
            for attr, value in new_data.items():
                setattr(self, attr, value)  # Dynamically set the new values
            self.save()  # Save the updates to the database
        else:
            adjustment_data = {
                "credit_line": self,
                "previous_credit_limit": self.credit_limit,
                "new_credit_limit": new_data.get("credit_limit", self.credit_limit),
                "previous_end_date": self.end_date,
                "new_end_date": new_data.get("end_date", self.end_date),
                "previous_status": self.status,
                "new_status": new_data.get("status", self.status),
                "previous_currency": self.currency,
                "new_currency": new_data.get("currency", self.currency),
                "reason": reason,
            }
            adjustment = CreditLineAdjustment(**adjustment_data)
            adjustment.full_clean()
            adjustment.save()

            # Update the CreditLine with the new data
            for attr, value in new_data.items():
                setattr(self, attr, value)
            self.save()

    class Meta:
        ordering = ["-created"]


class CreditLineAdjustment(models.Model):
    ADJUSTMENT_STATUS_CHOICES = (
        ("pending_review", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("implemented", "Implemented"),
    )
    credit_line = models.ForeignKey(
        CreditLine, related_name="adjustments", on_delete=models.CASCADE
    )
    previous_credit_limit = models.DecimalField(max_digits=12, decimal_places=2)
    new_credit_limit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    previous_end_date = models.DateField(null=True, blank=True)
    new_end_date = models.DateField(null=True, blank=True)
    previous_status = models.CharField(
        max_length=25, choices=CreditLine.CREDIT_LINE_STATUS
    )
    new_status = models.CharField(
        max_length=25, choices=CreditLine.CREDIT_LINE_STATUS, null=True, blank=True
    )
    previous_currency = models.CharField(
        max_length=5, choices=CreditLine.CURRENCY_OPTIONS
    )
    new_currency = models.CharField(
        max_length=5, choices=CreditLine.CURRENCY_OPTIONS, null=True, blank=True
    )
    adjustment_date = models.DateField(default=current_date)
    adjustment_status = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_STATUS_CHOICES,
        default="pending_review",
    )
    reason = models.TextField()

    def clean(self):
        # Validate new credit limit
        if self.new_credit_limit and self.new_credit_limit <= 0:
            raise ValidationError(
                {"new_credit_limit": "Credit limit must be greater than 0."}
            )

        # Ensure the new credit limit does not exceed max_digits
        if len(str(self.new_credit_limit).replace(".", "").replace("-", "")) > 12:
            raise ValidationError(
                {"new_credit_limit": "Credit limit must not exceed 12 digits."}
            )

        # Ensure the new end_date is not before the current start_date
        if self.new_end_date and self.credit_line.start_date >= self.new_end_date:
            raise ValidationError(
                {"new_end_date": "End date must be after the start date."}
            )

    def save(self, *args, **kwargs):
        if not self.pk:  # If this is a new adjustment and not an update
            # Automatically set the previous values from the associated CreditLine
            self.previous_credit_limit = self.credit_line.credit_limit
            self.previous_end_date = self.credit_line.end_date
            self.previous_status = self.credit_line.status
            self.previous_currency = self.credit_line.currency
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Adjustment for {self.credit_line} on {self.adjustment_date}"

    class Meta:
        ordering = ["-adjustment_date"]
