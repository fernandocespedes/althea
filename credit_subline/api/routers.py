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
    path(
        "adjustments/amount/create/<int:subline_pk>/",
        views.credit_amount_adjustment_create,
        name="credit_amount_adjustment_create",
    ),
    path(
        "adjustments/amount/adj-status/<int:adj_pk>/",
        views.credit_amount_adjustment_status_update,
        name="credit_amount_adjustment_status_update",
    ),
    path(
        "adjustments/interest-rate/create/<int:subline_pk>/",
        views.interest_rate_adjustment_create,
        name="interest_rate_adjustment_create",
    ),
    path(
        "adjustments/interest-rate/adj-status/<int:adj_pk>/",
        views.interest_rate_adjustment_status_update,
        name="interest_rate_adjustment_status_update",
    ),
    path(
        "adjustments/status/create/<int:subline_pk>/",
        views.credit_subline_status_adjustment_create,
        name="credit_subline_status_adjustment_create",
    ),
    path(
        "adjustments/status/adj-status/<int:adj_pk>/",
        views.credit_subline_status_adjustment_status_update,
        name="credit_subline_status_adjustment_status_update",
    ),
    path(
        "adjustments/list/",
        views.credit_subline_adjustments_admin_list,
        name="credit_subline_adjustments_admin_list",
    ),
    path(
        "adjustments/<str:type>/<int:adj_id>/",
        views.get_credit_subline_adjustment,
        name="get_credit_subline_adjustment",
    ),
]
