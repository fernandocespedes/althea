import credit_line.api.views as views
from django.urls import path

app_name = "credit_line_api"

urlpatterns = [
    path(
        "<int:pk>/",
        views.get_credit_line,
        name="get_credit_line",
    ),
    path(
        "list/",
        views.credit_lines_admin_list,
        name="credit_lines_admin_list",
    ),
    path(
        "adjustments/create/<int:pk>/",
        views.credit_line_adjustment_create,
        name="credit_line_adjustment_create",
    ),
    path(
        "adjustments/adjustment-status/update/<int:pk>/",
        views.credit_line_adjustment_status_update,
        name="credit_line_adjustment_status_update",
    ),
    path(
        "adjustments/list/",
        views.credit_line_adjustments_admin_list,
        name="credit_line_adjustments_admin_list",
    ),
    path(
        "adjustment/<int:pk>/",
        views.credit_line_adjustment_detail,
        name="credit_line_adjustment_detail",
    ),
]
