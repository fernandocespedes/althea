from django.urls import path
from . import views
from drf_yasg.utils import swagger_auto_schema
from .serializers import MyTokenObtainPairSerializer, UserSerializerWithToken

app_name = "accounts_api"


my_token_obtain_pair_view = swagger_auto_schema(
    method="post",
    request_body=MyTokenObtainPairSerializer,
    responses={400: "Bad Request", 201: UserSerializerWithToken},
)(views.MyTokenObtainPairView.as_view())


urlpatterns = [
    path("login/", my_token_obtain_pair_view, name="token_obtain_pair"),
    path("register/", views.register_user, name="register-user"),
    path(
        "activate-account/<uidb64>/<token>/<timestamp>/",
        views.activate_account_api,
        name="activate-account",
    ),
    path("reset-password/", views.forgot_password, name="forgot-password"),
    path(
        "reset-password/<uidb64>/<token>/<timestamp>/",
        views.reset_password_confirm,
        name="reset-password-confirm",
    ),
    path("profile/", views.get_user_profile, name="user-profile"),
    path("profile/update/", views.update_user_profile, name="user-profile-update"),
    path("list/", views.get_users, name="users-list"),
]
