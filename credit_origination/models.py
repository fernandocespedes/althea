from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class CreditType(models.Model):
    name = models.CharField(max_length=30)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created"]


class CreditRequest(models.Model):
    CREDIT_REQUEST_STATUS = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    credit_type = models.ForeignKey(
        CreditType, on_delete=models.SET_NULL, null=True, blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    term = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=25, choices=CREDIT_REQUEST_STATUS, default="pending"
    )

    def clean(self):
        # Ensure default field validation runs first
        self.clean_fields()

        if self.amount <= 0:
            raise ValidationError({"amount": "Amount must be greater than 0."})

        if len(str(self.amount).replace(".", "").replace("-", "")) > 12:
            raise ValidationError({"amount": "Amount must not exceed 12 digits."})

        if not (0 < self.term <= 120):
            raise ValidationError(
                {"term": "Term must be greater than 0 and less than or equal to 120."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} - {self.created} - {self.status}"

    class Meta:
        ordering = ["-created"]
