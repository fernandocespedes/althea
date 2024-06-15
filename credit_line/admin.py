from django.contrib import admin
from credit_line.models import CreditLine


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


admin.site.register(CreditLine, CreditLineAdmin)
