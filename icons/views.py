"""Views for icon system"""

from collections import defaultdict
from typing import Any, Dict, List

from django.views.generic import DetailView, ListView

from . import models


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        page = self.object
        assert isinstance(page, models.Page)

        context['icons'] = self.get_icons()
        context['folders'] = self.get_folder_modals()

        return context

    def get_folder_modals(self) -> List[Dict]:
        """Get the folder modals for template render"""

        page_folders = models.PageFolder.objects.filter(page=self.object)
        page_folder_rows = page_folders.values('folder__pk', 'folder__title')
        page_folder_ids = {d['folder__pk'] for d in page_folder_rows}

        folder_icons = models.FolderIcon.objects.filter(folder__pk__in=page_folder_ids)
        folder_icon_rows = folder_icons.values('folder__pk', 'icon__title', 'icon__icon', 'icon__url')

        folder_icons_by_folder_id = defaultdict(list)
        for row in folder_icon_rows:
            folder_icons_by_folder_id[row['folder__pk']].append({
                'title': row['icon__title'],
                'icon': row['icon__icon'],
                'url': row['icon__url'],
            })

        out = []
        for row in page_folder_rows:
            folder_id = row['folder__pk']
            icons = folder_icons_by_folder_id[folder_id]

            out.append({
                'id': folder_id,
                'title': row['folder__title'],
                'icons': icons
            })

        return out

    def get_icons(self) -> List[Dict]:
        """Get the icons for template display"""

        # The position of each object, so we can correlate the position with the sub-objects
        page_item_rows = []

        page_icons = models.PageIcon.objects.filter(page=self.object)
        for row in page_icons.values('position', 'icon__title', 'icon__icon', 'icon__url'):
            page_item_rows.append({
                'type': 'icon',
                'position': row['position'],
                'title': row['icon__title'],
                'icon': row['icon__icon'],
                'url': row['icon__url'],
            })

        page_folders = models.PageFolder.objects.filter(page=self.object)
        for row in page_folders.values('position', 'folder__pk', 'folder__title', 'folder__icon'):
            page_item_rows.append({
                'type': 'folder',
                'position': row['position'],
                'id': row['folder__pk'],
                'title': row['folder__title'],
                'icon': row['folder__icon'],
            })

        page_item_rows.sort(key=lambda obj: obj['position'])
        return page_item_rows


class PageList(ListView):
    """List of detail pages"""

    model = models.Page
