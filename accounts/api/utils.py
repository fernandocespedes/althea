from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import time
from django.contrib.auth import get_user_model
import re


User = get_user_model()


class AccountTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.password}{timestamp}"

    def make_token(self, user):
        token = super().make_token(user)
        return token

    def is_token_expired(self, timestamp):
        try:
            token_time = datetime.fromtimestamp(int(timestamp))
            current_time = datetime.now()
            time_elapsed = current_time - token_time
            return time_elapsed > timedelta(days=1)
        except ValueError:
            return True

    def generate_activation_link(self, user, base_url):
        """
        Generates a full link for a given user.

        :param user: User instance for which to generate the link.
        :param base_url: Base URL of the activation link
        (e.g., 'https://example.com/activate-account/')
        :return: Full URL string for user account activation.
        """
        user_id_encoded = urlsafe_base64_encode(force_bytes(user.pk))
        token = self.make_token(user)
        timestamp = int(datetime.now().timestamp())
        return f"{base_url}{user_id_encoded}/{token}/{timestamp}/"


account_token_generator = AccountTokenGenerator()


def send_user_email(request, user, mail_subject, email_template):
    """
    Sends an email to a user for various purposes such as account
    verification or password reset.

    Parameters:
    - request: HttpRequest object.
    - user: The user instance to whom the email is to be sent.
    - mail_subject: Subject of the email.
    - email_template: Path to the template used for the email body.
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    frontend_site = settings.FRONTEND_BASE_URL
    scheme = "https" if "https" in frontend_site else "http"
    message = render_to_string(
        email_template,
        {
            "user": user,
            "domain": frontend_site,
            "scheme": scheme,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_token_generator.make_token(user),
            "timestamp": int(time.time()),
        },
    )
    to_email = user.email
    mail = EmailMessage(mail_subject, message, from_email, to=[to_email])
    mail.content_subtype = "html"
    mail.send()


def generate_username(email, first_name, last_name):
    # Split the email to get the potential username
    username = email.split("@")[0].lower()

    # Check if a user with that username already exists
    if User.objects.filter(username=username).exists():
        username = (first_name + last_name).lower()

        # If there's still a conflict, append a sequence to make it unique
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = (original_username + str(counter)).lower()
            counter += 1

    return username


def custom_password_validator(value):
    if len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if not any(char.isdigit() for char in value):
        raise ValidationError("Password must contain at least one digit.")
    if not any(char.isupper() for char in value):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\'":\\|,.<>/?]', value):
        raise ValidationError("Password must contain at least one special character.")
