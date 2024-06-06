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
]
