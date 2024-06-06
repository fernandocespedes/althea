from django.db import models
from django.contrib.auth import get_user_model

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
