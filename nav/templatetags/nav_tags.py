"""Core template tags"""

from typing import List, Optional, Sequence
from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse, NoReverseMatch

from htmlBuilder import tags, attributes

from accounts.admin_staff_monkeypatch import patched_has_permission

register = template.Library()

ClassList = Optional[List[str]]


@register.simple_tag(takes_context=True)
def auth_button(context):
    """Logout button for nav"""

    request = context["request"]
    current_path = request.path
    current_user = request.user

    if current_user.is_anonymous:
        return _nav_item("Log in", reverse("accounts:login") + "?next=" + current_path)

    if current_user.is_hijacked:
        release_url = reverse("hijack:release")
        title = f"Release {current_user}"
        href = release_url + "?next=" + current_path
        hover = f"ID: {current_user.pk}&#013;Email: {current_user.email}"
        return _nav_item(title, href, link_classes=["link-form-post"], hover=hover)

    title = f"Log off {current_user}"
    href = reverse("accounts:logout") + "?next=" + current_path
    hover = f"ID: {current_user.pk}&#013;Email: {current_user.email}"
    return _nav_item(title, href, link_classes=["g_id_signout"], hover=hover)


@register.simple_tag(takes_context=True)
def nav_item(context, title: str, url_name: str, required_permission: str = None):
    """Determine if the active URL is the current URL"""

    request = context["request"]
    current_path = request.path

    if required_permission:
        if required_permission == "special:staff":
            if not patched_has_permission(request):
                return ""

        elif not request.user.has_perm(required_permission):
            return ""

    try:
        url = reverse(url_name)
    except NoReverseMatch:
        url = url_name
        return _nav_item(title, url)

    if url == current_path:
        return _nav_item(title, url, ["active"])

    return _nav_item(title, url)


def _nav_item(
    title,
    url,
    li_classes: ClassList = None,
    link_classes: ClassList = None,
    hover: str = "",
) -> str:
    """String for an available nav item"""

    li_class = _get_defaulted_classes(li_classes, "nav-item")
    a_class = _get_defaulted_classes(link_classes, "nav-link")

    li_attrs = [li_class]
    if hover:
        li_attrs.append(attributes.Title(hover))

    a_attrs = [a_class, attributes.Href(url)]

    li = tags.Li(li_attrs, tags.A(a_attrs, title))
    return mark_safe(li.render())


def _defaulted_list(extra_attrs: ClassList, *base_attrs: str) -> Sequence[str]:
    if not extra_attrs:
        return base_attrs

    return base_attrs + tuple(extra_attrs)


def _get_class(classes: Sequence[str]) -> attributes.Class:
    return attributes.Class(" ".join(classes))


def _get_defaulted_classes(
    extra_attrs: ClassList, *base_attrs: str
) -> attributes.Class:
    return _get_class(_defaulted_list(extra_attrs, *base_attrs))
