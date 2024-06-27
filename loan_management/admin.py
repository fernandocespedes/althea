from django.contrib import admin
from loan_management.models import LoanTerm, PeriodicPayment


class PeriodicPaymentInline(admin.TabularInline):
    model = PeriodicPayment
    extra = 0


class LoanTermInline(admin.TabularInline):
    model = LoanTerm
    extra = 0


class LoanTermAdmin(admin.ModelAdmin):
    list_display = [
        "credit_subline",
        "term_length",
        "repayment_frequency",
        "payment_due_day",
        "start_date",
        "status",
    ]
    list_filter = [
        "repayment_frequency",
        "payment_due_day",
        "start_date",
        "status",
    ]
    inlines = [
        PeriodicPaymentInline,
    ]


class PeriodicPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "loan_term",
        "due_date",
        "amount_due",
        "payment_status",
    ]
    list_filter = [
        "due_date",
        "payment_status",
        "actual_payment_date",
    ]


admin.site.register(LoanTerm, LoanTermAdmin)
admin.site.register(PeriodicPayment, PeriodicPaymentAdmin)
