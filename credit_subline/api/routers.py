import credit_subline.api.views as views
from django.urls import path

app_name = "credit_subline_api"

urlpatterns = [
    path(
        "create/<int:credit_line_pk>/",
        views.credit_subline_create,
        name="credit_subline_create",
    ),
    path(
        "list/",
        views.credit_sublines_admin_list,
        name="credit_sublines_admin_list",
    ),
    path(
        "<int:pk>/",
        views.get_credit_subline,
        name="get_credit_subline",
    ),
    path(
        "account/<int:credit_line_pk>/",
        views.get_account_credit_sublines,
        name="get_account_credit_sublines",
    ),
]
