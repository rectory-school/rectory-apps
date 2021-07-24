"""Views for icon system"""

from typing import Any, Dict

from django.views.generic import DetailView, ListView

from . import models


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        page = self.object
        assert isinstance(page, models.Page)

        # The position of each object, so we can correlate the position with the sub-objects
        page_item_rows = []

        for row in page.page_icons.all().values('position', 'icon__title', 'icon__icon', 'icon__url'):
            page_item_rows.append({
                'type': 'icon',
                'position': row['position'],
                'title': row['icon__title'],
                'icon': row['icon__icon'],
                'url': row['icon__url'],
            })

        for row in page.page_folders.all().values('position', 'folder__pk', 'folder__title', 'folder__icon'):
            page_item_rows.append({
                'type': 'folder',
                'position': row['position'],
                'id': row['folder__pk'],
                'title': row['folder__title'],
                'icon': row['folder__icon'],
            })

        page_item_rows.sort(key=lambda obj: obj['position'])

        context['icons'] = page_item_rows
        context['folders'] = {pf.folder: [fi.icon for fi in pf.folder.folder_icons.all()]
                              for pf in page.page_folders.all()}

        return context


class PageList(ListView):
    """List of detail pages"""

    model = models.Page
