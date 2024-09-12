"""Models for accounts"""

from typing import List
from string import ascii_letters, digits
from random import choice

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

CODE_CHARACTERS = ascii_letters + digits


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""

        if not email:
            raise ValueError("The given email must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_("email address"), unique=True)
    allow_google_hd_bypass = models.BooleanField(
        default=False,
        help_text="Allow Google login even if the user isn't in an allowed domain",
        verbose_name="Allow off-workspace Google login",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = []

    objects = UserManager()

    class Meta:
        """User metadata"""

        permissions = (("admin_login", "Can log into admin site"),)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"

        return self.email


def _random_code() -> str:
    return "".join(choice(CODE_CHARACTERS) for _ in range(48))


class TemporaryLoginCode(models.Model):
    """A temporary login authorization based on a link"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=48, unique=True, default=_random_code)
    expiration = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)


class LoginConfiguration(SingletonModel):
    enable_google_login = models.BooleanField(default=True)
    enable_email_login = models.BooleanField(default=False)
