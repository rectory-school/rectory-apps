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
        object_positions = {}

        for page_folder in page.page_folders.all():
            object_positions[page_folder.folder] = page_folder.position

        for page_icon in page.page_icons.all():
            object_positions[page_icon.icon] = page_icon.position

        # The dictionary keys are the original items
        all_items = sorted(object_positions, key=lambda obj: object_positions[obj])

        context['icons'] = all_items
        context['folders'] = {pf.folder: [fi.icon for fi in pf.folder.folder_icons.all()]
                              for pf in page.page_folders.all()}

        return context


class PageList(ListView):
    """List of detail pages"""

    model = models.Page
