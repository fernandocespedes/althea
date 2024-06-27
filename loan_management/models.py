from django.db import models
from credit_subline.models import CreditSubline
from django.core.exceptions import ValidationError
from credit_line.models import current_date
from decimal import Decimal


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


class PeriodicPayment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("delayed", "Delayed"),
    ]

    loan_term = models.ForeignKey(
        LoanTerm, on_delete=models.CASCADE, related_name="payments"
    )
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    principal_component = models.DecimalField(max_digits=10, decimal_places=2)
    interest_component = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    actual_payment_date = models.DateField(null=True, blank=True)

    def clean(self):
        # Ensuring all monetary values are positive
        if self.amount_due < Decimal("0.00"):
            raise ValidationError(
                {"amount_due": "Amount due must be a positive value."}
            )
        if self.principal_component < Decimal("0.00"):
            raise ValidationError(
                {"principal_component": "Principal component must be a positive value."}
            )
        if self.interest_component < Decimal("0.00"):
            raise ValidationError(
                {"interest_component": "Interest component must be a positive value."}
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.amount_due} - {self.due_date} | for loan term {self.loan_term.id}"
        )

    class Meta:
        ordering = ["due_date"]
