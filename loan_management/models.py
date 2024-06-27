from django.db import models
from credit_subline.models import CreditSubline
from django.core.exceptions import ValidationError
from credit_line.models import current_date


class LoanTerm(models.Model):
    REPAYMENT_FREQUENCIES = [
        ("biweekly", "Biweekly"),
        ("monthly", "Monthly"),
        ("bimonthly", "Bimonthly"),
        ("quarterly", "Quarterly"),
    ]
    STATUS_CHOICES = [
        ("approved", "Approved"),
        ("pending", "Pending"),
        ("rejected", "Rejected"),
    ]

    credit_subline = models.OneToOneField(CreditSubline, on_delete=models.CASCADE)
    term_length = models.PositiveIntegerField()
    repayment_frequency = models.CharField(max_length=10, choices=REPAYMENT_FREQUENCIES)
    payment_due_day = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    start_date = models.DateField(default=current_date)

    def clean(self):
        # Custom validation for payment_due_day
        if self.payment_due_day > 31:
            raise ValidationError(
                {"payment_due_day": "Payment due day must be 31 or less."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        created_str = self.created.strftime("%Y-%m-%d %H:%M:%S")
        return f"Loan Term for {self.credit_subline} on {created_str}"

    class Meta:
        ordering = ["-start_date"]
