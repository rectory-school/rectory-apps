"""Views for icon system"""

from typing import Any, Dict, List, Tuple

from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.views.generic import DetailView, ListView
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from django.urls import reverse

from . import models
from .view_types import Folder, FolderIcon, LinkIcon, Icon


@require_http_methods(["POST"])
@permission_required("icons.change_page")
def set_page_positions(request: HttpRequest):
    """Update the page positions of icons"""

    sorted_items = request.POST.getlist('sort[]')

    for i, item_key in enumerate(sorted_items):
        try:
            item_type, item_id = item_key.split("-")
            item_id = int(item_id)

            if item_type == "folder":
                models.PageFolder.objects.filter(pk=item_id).update(position=(i+1)*10)
            elif item_type == "icon":
                models.PageIcon.objects.filter(pk=item_id).update(position=(i+1)*10)
            else:
                return HttpResponseBadRequest()

        except ValueError:
            return HttpResponseBadRequest()

    messages.info(request, "Page icon positions saved successfully")
    return HttpResponse()


class PageDetail(DetailView):
    """Icon page embedded in site nav"""

    model = models.Page

    def get_queryset(self):
        qs = super().get_queryset()

        qs = qs.prefetch_related('page_folders',
                                 'page_folders__folder',
                                 'page_folders__folder__folder_icons',
                                 'page_folders__folder__folder_icons__icon',
                                 'page_icons',
                                 'page_icons__icon',
                                 'crosslinks',
                                 'crosslinks__crosslink',)

        return qs

    def get_context_data(self, **kwargs: Dict[str, Any]) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)

        page = self.object
        assert isinstance(page, models.Page)

        context['icons'] = self.get_icons()
        context['folders'] = self.get_folder_modals()

        crosslink_left, crosslink_right = self.get_crosslinks()

        context['crosslinks_left'] = crosslink_left
        context['crosslinks_right'] = crosslink_right
        context['sort_url'] = reverse('icons:set-sort-positions')

        return context

    def get_folder_modals(self) -> List[Folder]:
        """Get the folder modals for template render"""

        out = []

        for page_folder in self.object.page_folders.all():
            assert isinstance(page_folder, models.PageFolder)

            db_folder = page_folder.folder
            assert isinstance(db_folder, models.Folder)

            icons = []
            for folder_icon in db_folder.folder_icons.all():
                assert isinstance(folder_icon, models.FolderIcon)

                icon = folder_icon.icon
                assert isinstance(icon, models.Icon)

                icons.append(Icon(position=folder_icon.position, title=icon.title, icon=icon.icon))

            out.append(Folder(folder_id=db_folder.pk, title=db_folder.title, icons=icons))

        return out

    def get_icons(self) -> List[Icon]:
        """Get the icons for template display"""

        out = []
        for page_icon in self.object.page_icons.all():
            assert isinstance(page_icon, models.PageIcon)

            icon = page_icon.icon
            assert isinstance(icon, models.Icon)

            out.append(LinkIcon(position=page_icon.position,
                                title=icon.title,
                                icon=icon.icon,
                                url=icon.url,
                                page_icon_id=page_icon.pk))

        for page_folder in self.object.page_folders.all():
            assert isinstance(page_folder, models.PageFolder)

            folder = page_folder.folder
            assert isinstance(folder, models.Folder)

            out.append(FolderIcon(position=page_folder.position,
                                  folder_id=folder.id,
                                  title=folder.title,
                                  icon=folder.icon,
                                  page_folder_id=page_folder.id))

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


class PageList(ListView):
    """List of detail pages"""

    model = models.Page
