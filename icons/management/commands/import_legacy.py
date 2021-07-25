"""Import legacy icon data"""

import json
import os
import shutil

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from sorl.thumbnail import get_thumbnail

from icons import models


# pylint: disable=invalid-name,missing-class-docstring


class Command(BaseCommand):
    help = 'Import legacy icon data'

    def add_arguments(self, parser):
        parser.add_argument('legacy_file')

    def handle(self, *args, **options):
        # This is going to organize as d['paw_page'][1] = {'slug': 'student-icons', 'title': 'Student Icons'}
        organized_data = defaultdict(dict)

        with open(options['legacy_file']) as f_in:
            data = json.load(f_in)
            for row in data:
                organized_data[row['model']][row['pk']] = row['fields']

        print(organized_data.keys())
        organized_data = dict(organized_data)

        for file_name in os.listdir(settings.MEDIA_ROOT / "icons" / "original"):
            os.remove(settings.MEDIA_ROOT / "icons" / "original" / file_name)

        with transaction.atomic():
            models.Page.objects.all().delete()
            models.Folder.objects.all().delete()
            models.Icon.objects.all().delete()

            # Create folders
            for pk, fields in organized_data['paw.page'].items():
                slug = fields['slug']
                title = fields['title']

                models.Page.objects.create(pk=pk, slug=slug, title=title)

            # Create text links
            for pk, fields in organized_data['paw.pagetextlink'].items():
                text_link_fields = organized_data['paw.textlink'][fields['text_link']]

                page_link_id = text_link_fields['page_link']
                page_id = fields['page']

                models.CrossLink.objects.create(page_id=page_id,
                                                crosslink_id=page_link_id,
                                                side=fields['position'])

            # Create folders
            for pk, fields in organized_data['paw.pageicon'].items():
                if fields['classAttr'] != 'dialogLauncher':
                    continue

                _, icon_name = os.path.split(fields['display_icon'])
                full_icon_name = os.path.join("icons", "original", icon_name)

                shutil.copyfile(
                    os.path.join(settings.BASE_DIR / "scratch" / "icons-incoming" / icon_name),
                    os.path.join(settings.MEDIA_ROOT, "icons", "original", icon_name))

                models.Folder.objects.create(pk=pk, title=fields['title'], icon=full_icon_name)

            # Create icons
            for pk, fields in organized_data['paw.pageicon'].items():
                if fields['classAttr'] != 'iconLink':
                    continue

                _, icon_name = os.path.split(fields['display_icon'])
                full_icon_name = os.path.join("icons", "original", icon_name)

                shutil.copyfile(
                    os.path.join(settings.BASE_DIR / "scratch" / "icons-incoming" / icon_name),
                    os.path.join(settings.MEDIA_ROOT, "icons", "original", icon_name))

                models.Icon.objects.create(pk=pk, title=fields['title'], url=fields['href'], icon=full_icon_name)

            # Create folder icons
            for pk, fields in organized_data['paw.iconfoldericon'].items():
                models.FolderIcon.objects.create(
                    folder_id=fields['iconFolder'],
                    icon_id=fields['icon'],
                    position=fields['order'])

            # Create page icons
            for pk, fields in organized_data['paw.pageicondisplay'].items():
                original_row = organized_data['paw.pageicon'][fields['icon']]
                if original_row['classAttr'] == 'iconLink':
                    models.PageIcon.objects.create(
                        page_id=fields['page'],
                        icon_id=fields['icon'],
                        position=fields['order'])

                if original_row['classAttr'] == 'dialogLauncher':
                    models.PageFolder.objects.create(
                        page_id=fields['page'],
                        folder_id=fields['icon'],
                        position=fields['order'])
