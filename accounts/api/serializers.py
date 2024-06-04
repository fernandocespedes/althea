from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from accounts.api.utils import custom_password_validator


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer = UserSerializerWithToken(self.user).data
        for k, v in serializer.items():
            data[k] = v

        return data


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)

    class Meta:
        model = User
        # fields = '__all__'
        fields = [
            "id",
            "first_name",
            "last_name",
            "second_last_name",
            "full_name",
            "email",
            "username",
            "created",
            "is_active",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = [
            "id",
            "username",
            "created",
            "is_active",
            "is_staff",
            "is_superuser",
        ]


class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "second_last_name",
            "full_name",
            "email",
            "username",
            "created",
            "is_active",
            "is_staff",
            "is_superuser",
            "token",
        ]
        read_only_fields = [
            "id",
            "username",
            "created",
            "is_active",
            "is_staff",
            "is_superuser",
            "token",
        ]

    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return str(token.access_token)


class RegisterRequestSerializer(serializers.Serializer):
    first_name = serializers.CharField(help_text="First name of the user.")
    last_name = serializers.CharField(help_text="Last name of the user.")
    second_last_name = serializers.CharField(
        help_text="Second last name of the user.", required=False, allow_blank=True
    )
    email = serializers.EmailField(help_text="Email address of the user.")
    password = serializers.CharField(
        help_text="Password for the user.",
        write_only=True,
        validators=[
            custom_password_validator,
        ],
    )


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "No account with this email address exists."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[
            custom_password_validator,
        ],
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[
            custom_password_validator,
        ],
    )

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return data
