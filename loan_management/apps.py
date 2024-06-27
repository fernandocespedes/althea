from django.apps import AppConfig


class LoanManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "loan_management"

    def ready(self):
        import loan_management.signals  # noqa: F401
