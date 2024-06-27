from loan_management.models import LoanTerm, PeriodicPayment
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

_previous_loan_term_status = {}


@receiver(pre_save, sender=LoanTerm)
def capture_previous_loan_term_status(sender, instance, **kwargs):
    if instance is not None and instance.pk:
        try:
            # Get the current (old) value from the database
            old_instance = sender.objects.get(pk=instance.pk)
            _previous_loan_term_status[instance.pk] = old_instance.status
        except sender.DoesNotExist:
            # In case the instance does not exist yet, do nothing
            pass


@receiver(post_save, sender=LoanTerm)
def generate_periodic_payments(sender, instance, created, **kwargs):
    if instance is None or instance.status != "approved" or not instance.pk or created:
        return

    # Check if the status has changed from the previous approval
    previous_status = _previous_loan_term_status.get(instance.pk)
    if previous_status != "approved":
        # Importing inside function to avoid circular imports
        from loan_management.finance_utils import generate_amortization_schedule

        # Get LoanTerm data
        subline_amount = instance.credit_subline.subline_amount
        interest_rate = instance.credit_subline.interest_rate
        term_length = instance.term_length
        repayment_frequency = instance.repayment_frequency
        start_date_str = instance.start_date
        payment_due_day = instance.payment_due_day

        # Generate amortization schedule
        amortization_schedule = generate_amortization_schedule(
            subline_amount,
            interest_rate,
            term_length,
            repayment_frequency,
            start_date_str,
            payment_due_day,
        )

        # Populate PeriodicPayment model with the generated payments
        payments = []
        for index, row in amortization_schedule.iterrows():
            payment = PeriodicPayment(
                loan_term=instance,
                due_date=row["Payment Date"],
                amount_due=row["Total Payment"],
                principal_component=row["Principal"],
                interest_component=row["Interest"],
            )
            payments.append(payment)

        # Bulk create PeriodicPayment instances
        PeriodicPayment.objects.bulk_create(payments)
