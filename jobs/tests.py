from datetime import timedelta

from django.test import TestCase

from . import schedule, find_jobs


class ScheduleTest(TestCase):
    def test_registration(self):
        @schedule(timedelta(seconds=30))
        def hello():
            pass

        self.assertIn((timedelta(seconds=30), hello), find_jobs())

    def test_registration_int(self):
        @schedule(5)
        def hello():
            pass

        self.assertIn((timedelta(seconds=5), hello), find_jobs())
