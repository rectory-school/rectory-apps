"""Core template tags"""

from django import template
from django.utils.html import mark_safe
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def auth_button(context):
    """Logout button for nav"""

    request = context['request']
    current_path = request.path
    current_user = request.user

    if current_user.is_anonymous:
        return available_nav_item("Log in", reverse('accounts:login') + "?next=" + current_path)

    return available_nav_item("Log off " + str(current_user), reverse('accounts:logout') + "?next=" + current_path)


@register.simple_tag(takes_context=True)
def nav_item(context, title: str, url_name: str, required_permission: str = None):
    """Determine if the active URL is the current URL"""

    request = context['request']
    current_path = request.path

    if required_permission:
        if required_permission == "special:staff":
            if not request.user.is_staff:
                return ""

        elif not request.user.has_perm(required_permission):
            return ""

    try:
        url = reverse(url_name)
    except NoReverseMatch:
        url = url_name
        return available_nav_item(title, url)

    if url == current_path:
        return active_nav_item(title, url)

    return available_nav_item(title, url)


def active_nav_item(title, url) -> str:
    """String for an active nav item"""

    return mark_safe(f'<li class="nav-item active"><a class="nav-link" href="{url}">{ title }'
                     '<span class="sr-only">(current)</span></a></li>')


def available_nav_item(title, url) -> str:
    """String for an available nav item"""

    return mark_safe(f'<li class="nav-item"><a class="nav-link" href="{url}">{ title }</a></li>')
