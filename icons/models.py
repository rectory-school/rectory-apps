"""Models for icon system"""

import os
import uuid
from typing import Any
from django.core.exceptions import ValidationError

from django.db import models
from django.urls import reverse


def uuid_upload(instance: Any, filename: str, prefix="") -> str:
    """UUID unique upload paths"""

    del instance
    random_value = uuid.uuid4().hex
    _, ext = os.path.splitext(filename)

    return f"{prefix}{random_value}{ext}"


def icon_original_upload_to(instance: Any, filename: str) -> str:
    """Unique original icon upload path"""

    return uuid_upload(instance, filename, "icons/original/")


class Page(models.Model):
    """A page to show icons on"""

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Absolute URL to page detail"""

        return reverse("icons:page", kwargs={"slug": self.slug})


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
        # TODO: Put a manager on this that will always select related for the icon title

        return str(self.icon)


class PageItem(models.Model):
    """Display an icon on a page"""

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    icon = models.ForeignKey(Icon, on_delete=models.CASCADE, blank=True, null=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, blank=True, null=True)
    position = models.PositiveSmallIntegerField(default=0, blank=True, null=True)

    def clean(self):
        if not self.icon and not self.folder:
            raise ValidationError("Either a folder or an icon is required")

    class Meta:
        ordering = ['position']
        unique_together = (
            ('page', 'icon'),
        )

    def __str__(self):
        # TODO: Put a manager on this that will always select related for the icon title

        return str(self.icon)
