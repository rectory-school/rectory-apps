"""Views for icon system"""

from dataclasses import dataclass
from typing import Any, Dict, List, Iterable

from django.views.generic import DetailView

from . import models


@dataclass
class DisplayIcon:
    position: int
    title: str
    icon: Any
    href: str
    icon_class: str


CLASS_ICON = 'icon'


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        icons = models.PageIconDisplay.objects.filter(page=self.object).select_related('icon')
        context["icons"] = make_context_icon_set(icons)

        return context


def make_context_icon_set(page_icons: Iterable[models.PageIconDisplay]) -> List[DisplayIcon]:
    """Get the icon set, suitable for passing through context to icons/partial/icons.html"""

    out = []

    for page_icon in page_icons:
        icon = page_icon.icon
        assert isinstance(icon, models.Icon)

        obj = DisplayIcon(page_icon.position, icon.title, icon.icon, icon.url, CLASS_ICON)
        out.append(obj)

    return out
