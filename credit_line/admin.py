from django.contrib import admin
from credit_line.models import CreditLine, CreditLineAdjustment


class CreditLineAdjustmentInline(admin.TabularInline):
    model = CreditLineAdjustment
    extra = 0
    fields = [
        "previous_credit_limit",
        "new_credit_limit",
        "previous_end_date",
        "new_end_date",
        "previous_status",
        "new_status",
        "previous_currency",
        "new_currency",
        "adjustment_date",
        "reason",
    ]
    readonly_fields = [
        "previous_credit_limit",
        "previous_end_date",
        "previous_status",
        "previous_currency",
    ]


class CreditLineAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "credit_limit",
        "currency",
        "start_date",
        "end_date",
        "status",
        "created",
    )
    search_fields = ["credit_limit"]
    list_filter = ["currency", "created", "status"]
    inlines = [CreditLineAdjustmentInline]


class CreditLineAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        "credit_line",
        "new_credit_limit",
        "new_end_date",
        "new_status",
        "new_currency",
        "adjustment_date",
    ]


admin.site.register(CreditLine, CreditLineAdmin)
admin.site.register(CreditLineAdjustment, CreditLineAdjustmentAdmin)
