from django.apps import AppConfig


class CreditLineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "credit_line"

    def ready(self):
        import credit_line.signals  # noqa: F401
