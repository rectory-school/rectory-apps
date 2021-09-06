"""Basic tests"""

from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

import accounts.models
from . import models


class TestAPILinks(TestCase):
    """Follow all the API links down"""

    def test_unauthenticated(self):
        """Follow the top level of all the DRF views and make sure they are not accessible"""

        base_url = reverse('api-root')
        client = APIClient()
        entrypoints = client.get(base_url).json()

        for url in entrypoints.values():
            res = self.client.get(url)
            self.assertEqual(res.status_code, 401)

    def test_superuser(self):
        """Follow the top level of all the DRF views"""

        user = accounts.models.User.objects.create(email='root@localhost', is_superuser=True)
        user.refresh_from_db()

        client = APIClient()
        client.force_authenticate(user=user)

        base_url = reverse('api-root')
        entrypoints = client.get(base_url).json()

        for url in entrypoints.values():
            res = client.get(url)
            self.assertEqual(res.status_code, 200)


class TestManyStudents(TestCase):
    """Follow all the API links down"""

    def setUp(self) -> None:
        user = accounts.models.User.objects.create(email='root@localhost', is_superuser=True)
        self.client = APIClient()
        self.client.force_authenticate(user)

        objs = [models.Student(student_id=str(i),
                               first_name=f"First {i}",
                               last_name=f"Last {i}") for i in range(100000)]

        models.Student.objects.bulk_create(objs)

    def test_get_single_page(self):
        """Follow the top level of all the DRF views"""

        student_url = reverse('student-list')
        res = self.client.get(student_url).json()
        students = res["results"]
        self.assertEqual(len(students), 100)

    def test_get_all(self):
        """Follow the top level of all the DRF views"""

        next_url = reverse('student-list')

        students_by_url = {}

        while next_url:
            print(f"Loading {next_url}")
            res = self.client.get(next_url).json()

            next_url = res["next"]

            for record in res["results"]:
                students_by_url[record["url"]] = record

        self.assertEqual(len(students_by_url), 100000)
