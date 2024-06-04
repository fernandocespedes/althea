from accounts.api.serializers import (
    MyTokenObtainPairSerializer,
    UserSerializer,
    UserSerializerWithToken,
    RegisterRequestSerializer,
    ForgotPasswordSerializer,
    PasswordResetConfirmSerializer,
)
from accounts.api.utils import (
    send_user_email,
    account_token_generator,
    generate_username,
)
from django.db.utils import IntegrityError
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status


User = get_user_model()


class MyTokenObtainPairView(TokenObtainPairView):
    """
    Login to your account

    Use this endpoint to login to your account.

    If credentials are valid, the response will include a JWT that will let the user
    interact with other endpoints.
    """

    serializer_class = MyTokenObtainPairSerializer


@swagger_auto_schema(
    method="post",
    request_body=RegisterRequestSerializer,
    responses={400: "Bad Request", 201: UserSerializerWithToken},
)
@api_view(["POST"])
def register_user(request):
    """
    Register a new user.


    Use this endpoint to register a new user by providing the required details.
    """
    serializer = RegisterRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = request.data

    username = generate_username(data["email"], data["first_name"], data["last_name"])

    try:
        user = get_user_model().objects.create_user(
            first_name=data["first_name"],
            last_name=data["last_name"],
            second_last_name=data.get("second_last_name", ""),
            username=username,
            email=data["email"],
            password=data["password"],
        )

        # Send verification email
        mail_subject = "Complete Your Registration"
        email_template = "accounts/emails/account_verification_email.html"
        send_user_email(request, user, mail_subject, email_template)

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response(
            {"detail": "User with this email already exists"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        print(e)
        return Response(
            {"detail": "An error occurred while processing your request."},
            status=status.HTTP_400_BAD_REQUEST,
        )


@swagger_auto_schema(
    method="get", responses={200: "Activated Account", 401: "Unauthorized"}
)
@api_view(["GET"])
def activate_account_api(request, uidb64, token, timestamp):
    """
    Activate a user account.

    This endpoint is used to activate a user's account using a
    link with a uid, token, and timestamp. It marks the user's
    account as active if the link is valid and not expired.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return JsonResponse({"success": False, "message": "Invalid activation link"})

    # Check if the token has expired
    if account_token_generator.is_token_expired(timestamp):
        return JsonResponse(
            {"success": False, "message": "Activation link has expired"}
        )

    # Check if the user's account is already active
    if user.is_active:
        return JsonResponse({"success": False, "message": "Account already activated"})

    # Check if the token is valid
    if account_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return JsonResponse(
            {"success": True, "message": "Account activated successfully"}
        )
    else:
        return JsonResponse({"success": False, "message": "Invalid activation link"})


@swagger_auto_schema(
    method="post",
    request_body=ForgotPasswordSerializer,
    operation_description="Reset Password Email",
    operation_id="reset_password_email",
    responses={400: "Bad Request", 201: "Email sent to user"},
)
@api_view(["POST"])
def forgot_password(request):
    """
    Reset Password Email

    Send a password to the account to reset email.

    This endpoint accepts an email address and sends a password reset email if
    the email is associated with an active account.
    """
    email = request.data.get("email")
    user = get_user_model().objects.filter(email=email, is_active=True).first()

    if user:
        mail_subject = "Reset Your Password"
        email_template = "accounts/emails/password_reset_email.html"
        send_user_email(request, user, mail_subject, email_template)
        return JsonResponse(
            {"success": True, "message": "Password reset email sent successfully."}
        )
    else:
        return JsonResponse(
            {
                "success": False,
                "message": "No active account with this email address found.",
            },
            status=400,
        )


@swagger_auto_schema(
    method="post",
    request_body=PasswordResetConfirmSerializer,
    operation_description="Reset Password Confirm",
    operation_id="reset_password_confirm",
    responses={400: "Bad Request", 200: "Password successfully updated"},
)
@api_view(["POST"])
def reset_password_confirm(request, uidb64, token, timestamp):
    """
    Confirm the password reset.

    This endpoint finalizes the password reset process by accepting a new password
    along with a uid, token, and timestamp. It updates the user's password if
    the provided information is valid.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)

        if account_token_generator.is_token_expired(timestamp):
            return JsonResponse(
                {"success": False, "message": "Password reset link has expired"}
            )

        if not account_token_generator.check_token(user, token):
            return JsonResponse(
                {"success": False, "message": "Invalid password reset link"}, status=400
            )

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # Update the user's password
            new_password = serializer.validated_data["password"]
            user.set_password(new_password)
            user.save()
            return JsonResponse(
                {"success": True, "message": "Password updated successfully."}
            )
        else:
            return JsonResponse(
                {"success": False, "message": serializer.errors}, status=400
            )

    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
        return JsonResponse(
            {"success": False, "message": "Invalid password reset link"}, status=400
        )


@swagger_auto_schema(method="get", responses={200: UserSerializer, 401: "Unauthorized"})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Retrieve the authenticated user's profile.


    Use this endpoint to get the profile details of the currently authenticated user.
    """
    user = request.user
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)


@swagger_auto_schema(
    method="put",
    responses={200: UserSerializerWithToken, 401: "Unauthorized", 400: "Bad Request"},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Update the authenticated user's profile.

    Use this endpoint to update the profile details of the currently authenticated user.
    Updateable fields are: first_name, last_name, second_last_name, and email.
    """
    user = request.user
    serializer = UserSerializerWithToken(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="get",
    responses={200: UserSerializer(many=True), 401: "Unauthorized", 403: "Forbidden"},
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_users(request):
    """
    Retrieve a list of all users.

    Use this endpoint to get a list of all users. Only accessible by admin users.
    """
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)
