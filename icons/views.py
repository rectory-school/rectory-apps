"""Views for icon system"""

from typing import Any, Dict, List, Tuple

from django.views.generic import DetailView, ListView

from . import models
from .view_types import Folder, FolderIcon, LinkIcon, Icon


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        page = self.object
        assert isinstance(page, models.Page)

        context['icons'] = self.get_icons()
        context['folders'] = self.get_folder_modals()

        crosslink_left, crosslink_right = self.get_crosslinks()

        context['crosslinks_left'] = crosslink_left
        context['crosslinks_right'] = crosslink_right

        return context

    def get_folder_modals(self) -> List[Folder]:
        """Get the folder modals for template render"""

        folders_by_id = self._get_folder_skeletons()

        folder_icons = models.FolderIcon.objects.filter(folder__pk__in=folders_by_id.keys())
        for row in folder_icons.values('folder__pk', 'icon__title', 'icon__icon', 'icon__url'):
            folder_id = row['folder__pk']

            # Note: default sort is position, so we don't need to sort twice. Let the database do it.
            icon = LinkIcon(None, row['icon__title'], row['icon__icon'], row['icon__url'])
            folders_by_id[folder_id].icons.append(icon)

        return folders_by_id.values()

    def get_icons(self) -> List[Icon]:
        """Get the icons for template display"""

        out = []
        page_icons = models.PageIcon.objects.filter(page=self.object)
        for row in page_icons.values('position', 'icon__title', 'icon__icon', 'icon__url'):
            icon = LinkIcon(position=row['position'],
                            title=row['icon__title'],
                            icon=row['icon__icon'],
                            url=row['icon__url'])

            out.append(icon)

        page_folders = models.PageFolder.objects.filter(page=self.object)
        for row in page_folders.values('position', 'folder__pk', 'folder__title', 'folder__icon'):
            icon = FolderIcon(position=row['position'],
                              folder_id=row['folder__pk'],
                              title=row['folder__title'],
                              icon=row['folder__icon'])

            out.append(icon)

        out.sort(key=lambda obj: obj.position)
        return out

    def get_crosslinks(self) -> Tuple[List[models.Page], List[models.Page]]:
        """Return the left and right crosslinks"""

        left = []
        right = []

        for crosslink in self.object.crosslinks.all():
            assert isinstance(crosslink, models.CrossLink)

            if crosslink.side == "LEFT":
                left.append(crosslink.crosslink)

            if crosslink.side == "RIGHT":
                right.append(crosslink.crosslink)

        return (left, right)

    def _get_folder_skeletons(self) -> Dict[int, Folder]:
        """Get the folders without their icons, organized by folder ID"""

        page_folders = models.PageFolder.objects.filter(page=self.object)

        folders_by_id = {}
        for row in page_folders.values('folder__pk', 'folder__title'):
            folder = Folder(folder_id=row['folder__pk'], title=row['folder__title'])
            folders_by_id[folder.folder_id] = folder

        return folders_by_id


class PageList(ListView):
    """List of detail pages"""

    model = models.Page
