from django.contrib import admin
from loan_management.models import LoanTerm


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


admin.site.register(LoanTerm, LoanTermAdmin)
