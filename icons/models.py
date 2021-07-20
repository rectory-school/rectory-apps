"""Models for icon system"""

import os
import uuid
from typing import Any

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
        return reverse("icons:static-page", kwargs={"slug": self.slug})


class Icon(models.Model):
    """An icon that can be shown on a page"""

    title = models.CharField(max_length=255)
    url = models.URLField()
    icon = models.ImageField(upload_to=icon_original_upload_to)
    # icon = sorl.thumbnail.ImageField()

    def __str__(self):
        return self.title


class PageIconDisplay(models.Model):
    """Display an icon on a page"""

    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    icon = models.ForeignKey(Icon, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=0)
