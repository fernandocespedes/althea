from django.contrib import admin
from credit_subline.models import (
    CreditSubline,
    CreditAmountAdjustment,
    InterestRateAdjustment,
    CreditSublineStatusAdjustment,
)
from loan_management.admin import LoanTermInline


class CreditSublineInline(admin.TabularInline):
    model = CreditSubline
    extra = 0


class CreditAmountAdjustmentInline(admin.TabularInline):
    model = CreditAmountAdjustment
    extra = 0
    fields = [
        "initial_amount",
        "adjusted_amount",
        "effective_date",
        "reason_for_adjustment",
        "adjustment_status",
    ]
    readonly_fields = [
        "initial_amount",
    ]


class InterestRateAdjustmentInline(admin.TabularInline):
    model = InterestRateAdjustment
    extra = 0
    fields = [
        "initial_interest_rate",
        "adjusted_interest_rate",
        "effective_date",
        "reason_for_adjustment",
        "adjustment_status",
    ]
    readonly_fields = [
        "initial_interest_rate",
        "reason_for_adjustment",
    ]


class CreditSublineStatusAdjustmentInline(admin.TabularInline):
    model = CreditSublineStatusAdjustment
    extra = 0
    fields = [
        "initial_status",
        "adjusted_status",
        "effective_date",
        "reason_for_adjustment",
        "adjustment_status",
    ]
    readonly_fields = [
        "initial_status",
        "reason_for_adjustment",
    ]


class CreditSublineAdmin(admin.ModelAdmin):
    list_display = [
        "credit_line",
        "subline_type",
        "status",
    ]
    inlines = [
        CreditAmountAdjustmentInline,
        InterestRateAdjustmentInline,
        CreditSublineStatusAdjustmentInline,
        LoanTermInline,
    ]


admin.site.register(CreditSubline, CreditSublineAdmin)
