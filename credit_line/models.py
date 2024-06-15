from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


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

    class Meta:
        ordering = ["-created"]
