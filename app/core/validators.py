from django.contrib.auth import get_user_model
from django.core import validators
from django.utils.deconstruct import deconstructible
from rest_framework.exceptions import ValidationError

from app.core.models import Room


@deconstructible
class CustomUsernameValidator(validators.RegexValidator):
    regex = r'^[\w.+-]+\Z'
    message = 'Enter a valid username. This value may contain only letters, numbers, and ./+/-/_ characters.'
