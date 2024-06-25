from django.apps import AppConfig


class CreditSublineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "credit_subline"

    def ready(self):
        import credit_subline.signals  # noqa: F401
