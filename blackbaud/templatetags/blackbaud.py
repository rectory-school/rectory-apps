from typing import Dict, Optional
from django import template
from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from blackbaud.models import Teacher
from blackbaud.advising import get_advisees

register = template.Library()

GLOBAL_CACHE_KEY = "_cache"
IS_TEACHER_CACHE_KEY = "_is_teacher"
IS_ADVISOR_CACHE_KEY = "_is_advisor"


def _get_cache(context: Dict) -> Dict:
    if not GLOBAL_CACHE_KEY in context:
        context[GLOBAL_CACHE_KEY] = {}

    return context[GLOBAL_CACHE_KEY]


def _get_user(context: Dict) -> Optional[AbstractBaseUser]:
    request = context["request"]

    user: AbstractBaseUser | AnonymousUser = request.user

    if user.is_anonymous:
        return None

    return user


@register.simple_tag(takes_context=True)
def is_teacher(context) -> bool:
    cache = _get_cache(context)

    if IS_TEACHER_CACHE_KEY in cache:
        return cache[IS_TEACHER_CACHE_KEY]

    def get():
        user = _get_user(context)
        if not user:
            return False

        email = user.email
        if not email:
            return False

        return Teacher.objects.filter(email=email, active=True).exists()

    val = get()
    cache[IS_TEACHER_CACHE_KEY] = val
    return val


@register.simple_tag(takes_context=True)
def is_advisor(context) -> bool:
    cache = _get_cache(context)

    if IS_ADVISOR_CACHE_KEY in cache:
        return cache[IS_ADVISOR_CACHE_KEY]

    def get():
        user = _get_user(context)

        if not user:
            return False

        email = user.email
        if not email:
            return False

        teachers = Teacher.objects.filter(email=email, active=True)
        advisees = get_advisees(teachers)

        if advisees:
            return True

        return False

    val = get()
    cache[IS_ADVISOR_CACHE_KEY] = val
    return val
