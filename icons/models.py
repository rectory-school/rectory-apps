"""Models for icon system"""

import os
import uuid
from typing import Any

from django.db import models
from django.urls import reverse

FOLDER_MODAL_ID_PREFIX = "folder-model"


def uuid_upload(instance: Any, filename: str, prefix="") -> str:
    """UUID unique upload paths"""

    del instance
    random_value = uuid.uuid4().hex
    _, ext = os.path.splitext(filename)

    return f"{prefix}{random_value}{ext}"


def icon_original_upload_to(instance: Any, filename: str) -> str:
    """Unique original icon upload path"""

    return uuid_upload(instance, filename, "icons/original/")


class Icon(models.Model):
    """An icon that can be shown on a page"""

    title = models.CharField(max_length=255)
    url = models.URLField()
    icon = models.ImageField(upload_to=icon_original_upload_to)

    def __str__(self):
        return self.title


class Folder(models.Model):
    """A reusable folder"""

    title = models.CharField(max_length=255)
    icon = models.ImageField(upload_to=icon_original_upload_to)

    def __str__(self):
        return self.title


class FolderIcon(models.Model):
    """An icon in a folder"""

    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='folder_icons')
    icon = models.ForeignKey(Icon, on_delete=models.CASCADE, related_name='+')
    position = models.PositiveSmallIntegerField(default=0, blank=True, null=True)

    class Meta:
        ordering = ['position']
        unique_together = (
            ('folder', 'icon'),
        )

    def __str__(self):
        return str(self.icon)


class Page(models.Model):
    """A page to show icons on"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Absolute URL to page detail"""

        return reverse("icons:page", kwargs={"slug": self.slug})


class TextLink(models.Model):
    """Text link on the bottom of a page"""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='text_links')
    url = models.URLField(blank=True)
    crosslink = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='+')


class PageIcon(models.Model):
    """An icon on a page"""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='page_icons')
    icon = models.ForeignKey(Icon, on_delete=models.CASCADE, related_name='+')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position']
        unique_together = ('page', 'icon')

    def __str__(self):
        return str(self.icon)


class PageFolder(models.Model):
    """A folder on a page"""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='page_folders')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='+')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position']
        unique_together = ('page', 'folder')

    def __str__(self):
        return str(self.folder)
