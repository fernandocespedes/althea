from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from credit_line.models import CreditLineAdjustment
from django.utils import timezone

# This dictionary will hold the previous status values temporarily
_previous__adjustment_statuses = {}


@receiver(pre_save, sender=CreditLineAdjustment)
def capture_previous_adjustment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            # Get the current (old) value from the database
            old_instance = sender.objects.get(pk=instance.pk)
            _previous__adjustment_statuses[instance.pk] = old_instance.adjustment_status
        except sender.DoesNotExist:
            # In case the instance does not exist yet, do nothing
            pass


@receiver(post_save, sender=CreditLineAdjustment)
def update_credit_line_on_approval(sender, instance, **kwargs):
    previous_status = _previous__adjustment_statuses.pop(instance.pk, None)

    if instance.adjustment_status == "approved" and previous_status != "approved":

        def process_adjustment():
            with transaction.atomic():
                adjustment_data = {}

                # Check each field for changes and add them to the adjustment_data if not None
                if instance.new_credit_limit is not None:
                    adjustment_data["credit_limit"] = instance.new_credit_limit
                if instance.new_end_date is not None:
                    adjustment_data["end_date"] = instance.new_end_date
                if instance.new_status is not None:
                    adjustment_data["status"] = instance.new_status
                if instance.new_currency is not None:
                    adjustment_data["currency"] = instance.new_currency

                # Only make adjustments if there's actually something to adjust
                if adjustment_data:
                    # Use update_only=True to directly update the CreditLine
                    instance.credit_line.make_adjustment(
                        adjustment_data,
                        "Automatic adjustment on approval",
                        update_only=True,
                    )

                    # Now update the adjustment_date on the CreditLineAdjustment instance
                    # to the current date, since all adjustments are implemented
                    instance.adjustment_status = "implemented"
                    instance.adjustment_date = timezone.now().date()
                    instance.save()

            # Schedule the adjustment to be processed after the transaction commits

        transaction.on_commit(process_adjustment)
