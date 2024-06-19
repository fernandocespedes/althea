from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from credit_origination.models import CreditRequest
from credit_line.models import CreditLine


@receiver(pre_save, sender=CreditRequest)
def capture_previous_status(sender, instance, **kwargs):
    if instance.pk:
        previous = CreditRequest.objects.get(pk=instance.pk)
        instance._previous_status = previous.status


@receiver(post_save, sender=CreditRequest)
def create_credit_line(sender, instance, created, **kwargs):
    if not created:
        if (
            hasattr(instance, "_previous_status")
            and instance.status == "approved"
            and instance._previous_status != "approved"
        ):
            CreditLine.objects.get_or_create(
                user=instance.user,
                defaults={
                    "credit_limit": instance.amount,
                    "start_date": timezone.now().date(),
                    "status": "pending",
                },
            )

        # If you want, you could send an email for admin notification
