from django.contrib import admin
from credit_origination.models import CreditType


class CreditTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created", "active")
    search_fields = ["name"]
    list_filter = ["name"]


admin.site.register(CreditType, CreditTypeAdmin)
