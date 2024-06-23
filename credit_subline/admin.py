from django.contrib import admin
from credit_subline.models import CreditSubline


class CreditSublineInline(admin.TabularInline):
    model = CreditSubline
    extra = 0


class CreditSublineAdmin(admin.ModelAdmin):
    list_display = [
        "credit_line",
        "subline_type",
        "status",
    ]


admin.site.register(CreditSubline, CreditSublineAdmin)
