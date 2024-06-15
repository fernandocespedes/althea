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
]
