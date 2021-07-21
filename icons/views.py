"""Views for icon system"""

from dataclasses import dataclass
from typing import Any, Dict, List, Iterable, Tuple

from django.views.generic import DetailView, ListView

from . import models


@dataclass
class DisplayIcon:
    """An icon to be displayed on a page"""

    title: str
    icon: Any
    href: str
    icon_class: str


CLASS_ICON = 'icon'
CLASS_FOLDER = 'folder'
FOLDER_ID_PREFIX = 'folder-'


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        all_page_items = models.PageItem.objects.filter(page=self.object).values('position'
                                                                                 'icon__pk',
                                                                                 'icon__title',
                                                                                 'icon__url',
                                                                                 'icon__icon',
                                                                                 'folder__pk',
                                                                                 'folder__title',
                                                                                 'folder__icon')

        all_folder_ids = {row['folder__pk'] for row in all_page_items if row['folder__pk']}

        all_folder_icons = models.FolderIcon.objects.filter(folder__pk__in=all_folder_ids).values('position',
                                                                                                  'folder__pk',
                                                                                                  'folder__title',
                                                                                                  'icon__pk',
                                                                                                  'icon__title',
                                                                                                  'icon__url',
                                                                                                  'icon__icon')

        icons = models.PageItem.objects.filter(page=self.object).select_related('icon', 'folder')
        folders = models.Folder.objects.filter(
            pageitem__page=self.object).prefetch_related(
            'folder_icons', 'folder_icons__icon')

        context["icons"] = make_context_icon_set(icons)
        context["folders"] = make_context_folders(folders)
        return context


class PageList(ListView):
    """List of detail pages"""

    model = models.Page


def make_context_icon_set(page_items: Iterable[models.PageItem]) -> List[DisplayIcon]:
    """Get the icon set, suitable for passing through context to icons/partial/icons.html"""

    out = []

    for page_item in page_items:
        if page_item.icon:
            icon = page_item.icon
            assert isinstance(icon, models.Icon)

            obj = DisplayIcon(icon.title, icon.icon, icon.url, CLASS_ICON)

        elif page_item.folder:
            folder = page_item.folder
            assert isinstance(folder, models.Folder)

            obj = DisplayIcon(folder.title, folder.icon, f"#{FOLDER_ID_PREFIX}{folder.pk}", CLASS_FOLDER)

        out.append(obj)

    return out


def make_context_folder(folder_icons: Iterable[models.FolderIcon]) -> Iterable[DisplayIcon]:
    """Get the icon set for a folder, suitable for passing through context to icons/partial/icons.html"""

    for folder_icon in folder_icons:
        icon = folder_icon.icon
        assert isinstance(icon, models.Icon)

        yield DisplayIcon(icon.title, icon.icon, icon.url, CLASS_ICON)


def make_context_folders(folders: Iterable[models.Folder]) -> Iterable[Tuple[str, str, Iterable[DisplayIcon]]]:
    """Get the icons sets for a bunch of folders, suitable for context to the static display"""

    for folder in folders:
        yield f"{FOLDER_ID_PREFIX}-{folder.pk}", folder.title, make_context_folder(folder.folder_icons.all())
