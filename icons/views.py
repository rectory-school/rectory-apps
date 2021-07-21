"""Views for icon system"""

from functools import cached_property

from dataclasses import dataclass
from typing import Any, Dict, List, Iterable, Optional, Set

from django.views.generic import DetailView, ListView

from . import models


@dataclass
class DisplayIcon:
    """An icon to be displayed on a page"""

    title: str
    icon: Any
    href: str


CLASS_ICON = 'icon'
CLASS_FOLDER = 'folder'
FOLDER_ID_PREFIX = 'folder-'


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context_manager = IconManager(self.object)

        context["icons"] = context_manager.icons
        context["folders"] = context_manager.folders
        context["folder_id_prefix"] = FOLDER_ID_PREFIX

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


@dataclass
class Icon:
    """An icon that can be shown on the partial icon template"""

    title: str
    icon: str
    href: str


@dataclass
class Folder:
    """A folder with icons to show in a modal"""

    id: str  # pylint: disable=invalid-name
    title: str
    icons: List[Icon]


@dataclass
class PageItem:
    """Thin wrapper for a page item, straight from the values call"""

    position: int

    icon__pk: Optional[int]
    icon__title: Optional[str]
    icon__icon: Optional[str]
    icon__url: Optional[str]

    folder__pk: Optional[int]
    folder__title: Optional[str]
    folder__icon: Optional[str]

    @property
    def icon(self) -> Optional[Icon]:
        """Get the underlying icon"""

        # Will either give back an link to launch, or a modal to pop up

        if self.icon__pk:
            return Icon(self.icon__title, self.icon__icon, self.icon__url)

        if self.folder__pk:
            return Icon(self.folder__title, self.folder__icon, f"#{FOLDER_ID_PREFIX}{self.folder__pk}")

        return None


@dataclass
class FolderIcon:
    """Thin wrapper for a folder icon, straight from the values call"""

    position: int
    folder__pk: int
    icon__pk: int
    icon__title: str
    icon__url: str
    icon__icon: str

    @property
    def icon(self) -> Icon:
        """Get the underlying icon"""

        return Icon(self.icon__title, self.icon__icon, self.icon__url)


class IconManager:
    """Class with helpers to make sense of icon data"""

    def __init__(self, page: models.Page):
        self.page = page

    @cached_property
    def page_items(self) -> List[PageItem]:
        """Get all the page items"""

        all_page_items = models.PageItem.objects.filter(page=self.page)
        page_item_values = list(all_page_items.values('position', 'icon__pk', 'icon__title', 'icon__url', 'icon__icon',
                                                      'folder__pk', 'folder__title', 'folder__icon'))
        page_item_values.sort(key=lambda row: row['position'])

        return [PageItem(**row) for row in page_item_values]

    @cached_property
    def icons(self) -> List[Icon]:
        """Icons for display"""

        return [page_item.icon for page_item in self.page_items if page_item.icon]

    @cached_property
    def all_folder_ids(self) -> Set[int]:
        """Get all the folder IDs in this page item"""

        return {item.folder__pk for item in self.page_items if item.folder__pk}

    @cached_property
    def folders(self) -> List[Folder]:
        """All folders for modal generation"""

        all_folder_icons = models.FolderIcon.objects.filter(folder__pk__in=self.all_folder_ids)
        folder_icon__values = all_folder_icons.values('position', 'folder__pk', 'folder__title',
                                                      'icon__pk', 'icon__title', 'icon__url', 'icon__icon')

        folders_by_id = {}
        for row in sorted(folder_icon__values, key=lambda row: (row['folder__pk'], row['position'])):
            folder_id = row['folder__pk']

            try:
                folder = folders_by_id[row[folder_id]]
            except KeyError:
                folder = Folder(f"{FOLDER_ID_PREFIX}{folder_id}", row['folder__title'], [])
                folders_by_id[folder.id] = folder

            folder.icons.append(Icon(row['icon__title'], row['icon__icon'], row['icon__url']))

        return folders_by_id.values()
