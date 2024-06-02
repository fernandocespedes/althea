# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer  # , UserSerializerWithToken,


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Login to your account

    Use this endpoint to login to your account.

    If credentials are valid, the response will include a JWT that will let the user
    interact with other endpoints.
    """

    serializer_class = MyTokenObtainPairSerializer
