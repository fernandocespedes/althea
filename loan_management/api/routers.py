import loan_management.api.views as views
from django.urls import path

app_name = "loan_management_api"

urlpatterns = [
    path(
        "create/<int:subline_pk>/",
        views.loan_term_create,
        name="loan_term_create",
    ),
    path(
        "status/update/<int:loan_term_pk>/",
        views.loan_term_status_update,
        name="loan_term_status_update",
    ),
    path(
        "<int:loan_term_pk>/",
        views.loan_term_detail,
        name="loan_term_detail",
    ),
]
