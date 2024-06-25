from django.db.models.signals import pre_save, post_save
from credit_subline.models import (
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from django.utils import timezone
from django.db import transaction
from django.dispatch import receiver

_previous__amount_adjustment_statuses = {}


@receiver(pre_save, sender=CreditAmountAdjustment)
def capture_previous_amount_adjustment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            # Get the current (old) value from the database
            old_instance = sender.objects.get(pk=instance.pk)
            _previous__amount_adjustment_statuses[instance.pk] = (
                old_instance.adjustment_status
            )
        except sender.DoesNotExist:
            # In case the instance does not exist yet, do nothing
            pass


@receiver(post_save, sender=CreditAmountAdjustment)
def update_credit_subline_amount_on_approval(sender, instance, **kwargs):
    previous_status = _previous__amount_adjustment_statuses.pop(instance.pk, None)

    # Only proceed if the instance was approved and the previous status was not "approved"
    if instance.adjustment_status == "approved" and previous_status != "approved":

        def process_adjustment():
            with transaction.atomic():
                if instance.adjusted_amount is not None:
                    credit_subline = instance.credit_subline
                    credit_subline.subline_amount = instance.adjusted_amount
                    credit_subline.save()

                # update the adjustment_status to "implemented" and the effective_date
                instance.adjustment_status = "implemented"
                instance.effective_date = timezone.now().date()
                instance.save()

        transaction.on_commit(process_adjustment)


_previous__interest_rate_adjustment_statuses = {}


@receiver(pre_save, sender=InterestRateAdjustment)
def capture_previous_interest_rate_adjustment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            # Get the current (old) value from the database
            old_instance = sender.objects.get(pk=instance.pk)
            _previous__interest_rate_adjustment_statuses[instance.pk] = (
                old_instance.adjustment_status
            )
        except sender.DoesNotExist:
            # In case the instance does not exist yet, do nothing
            pass


@receiver(post_save, sender=InterestRateAdjustment)
def update_credit_subline_interest_rate_on_approval(sender, instance, **kwargs):
    previous_status = _previous__interest_rate_adjustment_statuses.pop(
        instance.pk, None
    )

    # Only proceed if the instance was approved and the previous status was not "approved"
    if instance.adjustment_status == "approved" and previous_status != "approved":

        def process_adjustment():
            with transaction.atomic():
                if instance.adjusted_interest_rate is not None:
                    credit_subline = instance.credit_subline
                    credit_subline.interest_rate = instance.adjusted_interest_rate
                    credit_subline.save()

                # update the adjustment_status to "implemented" and the effective_date
                instance.adjustment_status = "implemented"
                instance.effective_date = timezone.now().date()
                instance.save()

        transaction.on_commit(process_adjustment)


_previous__credit_subline_status_adjustment_statuses = {}


@receiver(pre_save, sender=CreditSublineStatusAdjustment)
def capture_previous_subline_status_adjustment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            # Get the current (old) value from the database
            old_instance = sender.objects.get(pk=instance.pk)
            _previous__credit_subline_status_adjustment_statuses[instance.pk] = (
                old_instance.adjustment_status
            )
        except sender.DoesNotExist:
            # In case the instance does not exist yet, do nothing
            pass


@receiver(post_save, sender=CreditSublineStatusAdjustment)
def update_credit_subline_status_on_approval(sender, instance, **kwargs):
    previous_status = _previous__credit_subline_status_adjustment_statuses.pop(
        instance.pk, None
    )

    # Only proceed if the instance was approved and the previous status was not "approved"
    if instance.adjustment_status == "approved" and previous_status != "approved":

        def process_adjustment():
            with transaction.atomic():
                if instance.adjusted_status is not None:
                    credit_subline = instance.credit_subline
                    credit_subline.status = instance.adjusted_status
                    credit_subline.save()

                # update the adjustment_status to "implemented" and the effective_date
                instance.adjustment_status = "implemented"
                instance.effective_date = timezone.now().date()
                instance.save()

        transaction.on_commit(process_adjustment)
