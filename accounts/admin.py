from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin


class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "first_name",
        "last_name",
        "second_last_name",
        "is_active",
        "is_staff",
    )
    search_fields = ("first_name", "last_name", "second_last_name", "email", "username")
    ordering = ("-created",)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(User, CustomUserAdmin)
