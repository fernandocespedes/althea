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
]
