"""Views for icon system"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from django.views.generic import DetailView, ListView

from . import models


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        assert isinstance(self.object, models.Page)

        icons = make_icon_links(self.object)
        all_folder_ids = {page_item.folder.folder_id for page_item in icons if page_item.folder}
        folders = make_folders(all_folder_ids)

        context["icons"] = icons
        context["folders"] = folders

        return context


class PageList(ListView):
    """List of detail pages"""

    model = models.Page


@dataclass
class IconLink:
    """An icon link on the page"""

    title: str
    url: str
    icon: str


@dataclass
class FolderLink:
    """A folder link on the page"""

    folder_id: int
    title: str
    icon: str


@dataclass
class CompoundLink:
    """An icon and/or folder link"""

    icon: Optional[IconLink]
    folder: Optional[FolderLink]


@dataclass
class Folder:
    """A folder that can be displayed in a modal"""

    folder_id: int
    title: str
    icons: List[IconLink]


def make_icon_links(page: models.Page) -> List[CompoundLink]:
    """Make the page items for a page without the Django ORM"""

    rows = page.items.all().values('icon__pk',
                                   'icon__title',
                                   'icon__icon',
                                   'icon__url',
                                   'folder__pk',
                                   'folder__title',
                                   'folder__icon')

    return [make_page_item(row) for row in rows]


def make_page_item(row: dict) -> CompoundLink:
    """Translate rows from PageItem into the PageItem dataclass"""

    icon = None
    folder = None
    if row['icon__pk']:
        icon = IconLink(row['icon__title'], row['icon__url'], row['icon__icon'])

    if row['folder__pk']:
        folder = FolderLink(row['folder__pk'], row['folder__title'], row['folder__icon'])

    return CompoundLink(icon, folder)


def make_folders(folder_ids: Set[int]) -> Dict[int, Folder]:
    """Make the folders for partial/folders.html from a list of folder IDs"""

    rows = models.FolderIcon.objects.filter(folder__pk__in=folder_ids)
    rows = rows.values('folder__pk',
                       'folder__title',
                       'icon__title',
                       'icon__url',
                       'icon__icon')

    folders_by_id = {}

    for row in rows:
        folder_id = row['folder__pk']

        try:
            folder = folders_by_id[folder_id]
        except KeyError:
            folder_title = row['folder__title']

            folder = Folder(folder_id, folder_title, [])
            folders_by_id[folder_id] = folder

        icon = IconLink(row['icon__title'], row['icon__url'], row['icon__icon'])
        folder.icons.append(icon)

    return folders_by_id
