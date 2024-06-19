from django.apps import AppConfig


class CreditOriginationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "credit_origination"

    def ready(self):
        import credit_origination.signals  # noqa: F401
