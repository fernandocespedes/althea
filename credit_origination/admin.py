from django.contrib import admin
from credit_origination.models import CreditType, CreditRequest


class CreditTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created", "active")
    search_fields = ["name"]
    list_filter = ["name"]


class CreditRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "credit_type", "amount", "term", "status", "created")
    search_fields = ["user__email", "credit_type__name", "status"]
    list_filter = ["status", "credit_type", "created"]


class CreditRequestInline(admin.TabularInline):
    model = CreditRequest
    extra = 0
    fields = ("credit_type", "amount", "term", "status", "created")
    readonly_fields = ("created",)


admin.site.register(CreditType, CreditTypeAdmin)
admin.site.register(CreditRequest, CreditRequestAdmin)
