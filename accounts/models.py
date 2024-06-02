from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(
        self,
        first_name,
        last_name,
        username,
        email,
        second_last_name=None,
        phone_number=None,
        password=None,
    ):
        if not email:
            raise ValueError("All users must have an email associated to the account")

        if not username:
            raise ValueError("All users must have a username associated to the account")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            second_last_name=second_last_name,
            phone_number=phone_number,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        first_name,
        last_name,
        username,
        email,
        second_last_name=None,
        phone_number=None,
        password=None,
    ):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            second_last_name=second_last_name,
            phone_number=phone_number,
            password=password,
        )
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    second_last_name = models.CharField(max_length=50, null=True, blank=True)
    username = models.CharField(
        max_length=50, unique=True, verbose_name="Nombre de Usuario"
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # required fields
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="user_set",
        related_query_name="user",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="user_set",
        related_query_name="user",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def full_name(self):
        if self.second_last_name:
            return f"{self.first_name} {self.last_name} {self.second_last_name}"
        else:
            return f"{self.first_name} {self.last_name}"
