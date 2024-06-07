import credit_origination.api.views as views
from django.urls import path

app_name = "credit_origination_api"

urlpatterns = [
    path(
        "credit-types/create/",
        views.credit_type_create,
        name="credit_type_create",
    ),
    path(
        "credit-types/<int:pk>/update/",
        views.credit_type_update,
        name="credit_type_update",
    ),
    path(
        "credit-types/",
        views.credit_type_list,
        name="credit_type_list",
    ),
    path(
        "credit-types/admin/",
        views.admin_credit_type_list,
        name="admin_credit_type_list",
    ),
    path(
        "credit-types/<int:pk>/delete/",
        views.delete_credit_type,
        name="credit_type_delete",
    ),
    path(
        "credit-requests/user/create/",
        views.create_user_credit_request,
        name="create_user_credit_request",
    ),
    path(
        "credit-requests/user/<int:pk>/",
        views.update_user_credit_request,
        name="update_user_credit_request",
    ),
    path(
        "credit-requests/list/",
        views.credit_requests_admin_list,
        name="credit_requests_admin_list",
    ),
    path(
        "credit-requests/account/list/",
        views.list_credit_requests,
        name="list_credit_requests",
    ),
    path(
        "credit-requests/status/update/<int:pk>/",
        views.credit_request_status_update,
        name="credit_request_status_update",
    ),
]
