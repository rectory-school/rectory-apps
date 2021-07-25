"""Import legacy icon data"""

import json
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

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

        with transaction.atomic():
            models.Page.objects.all().delete()
            models.Folder.objects.all().delete()
            models.Icon.objects.all().delete()

            for pk, fields in organized_data['paw.page'].items():
                slug = fields['slug']
                title = fields['title']

                models.Page.objects.create(pk=pk, slug=slug, title=title)

            for pk, fields in organized_data['paw.pagetextlink'].items():

                text_link_fields = organized_data['paw.textlink'][fields['text_link']]
                
                page_link_id = text_link_fields['page_link']
                page_id = fields['page']

                models.CrossLink.objects.create(page_id=page_id,
                                                crosslink_id=page_link_id,
                                                side=fields['position'])
