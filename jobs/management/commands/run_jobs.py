from typing import List
from threading import Thread, Event, Lock
import time

import logging
from datetime import datetime, timedelta
import signal

from django.core.management.base import BaseCommand

from jobs import find_jobs, Job

log = logging.getLogger(__name__)


class JobThread(Thread):
    def __init__(self, interval: timedelta, job: Job):
        self.interval = interval
        self.job = job
        self.full_name = f"{self.job.__module__}.{self.job.__name__}"

        self._stopping = Event()

        super().__init__()

    def run(self):
        log.info("Thread for %s executing evert %s started", self.full_name, self.interval)

        while not self._stopping.is_set():
            log.info("Starting %s", self.full_name)
            started_at = datetime.now()

            try:
                self.job()
            except Exception as exc:
                log.exception("Exception when running job %s", self.full_name)

            log.info("Finished %s", self.full_name)

            next_run = started_at + self.interval
            now = datetime.now()
            delay = next_run - now

            if delay > timedelta(seconds=0):
                log.info("%s not ready to be run, waiting %s", self.full_name, delay)

                # Wait until stopping is set, in which case the while loop will exit,
                # or until the next run time
                if self._stopping.wait(delay.total_seconds()):
                    return
            else:
                log.info("%s being run with no delay", self.full_name)

        log.info("Thread running %s stopped", self.full_name)

    def stop(self):
        self._stopping.set()


class Coordinator(Thread):
    def __init__(self):
        self.evt = Event()
        self.workers: List[JobThread] = []
        self._lock = Lock()

        super().__init__()

    def run(self):
        log.info("Job tracker thread started")
        self.evt.wait()
        log.info("Job tracker thread beginning shutdown")

        for worker in self.workers:
            worker.stop()

        for worker in self.workers:
            log.info("Waiting for %s shutdown", worker.full_name)
            worker.join()
            log.info("%s shutdown finished", worker.full_name)

        log.info("Job tracker thread finished")

    def add(self, interval: timedelta, job: Job):
        with self._lock:
            thread = JobThread(interval, job)
            self.workers.append(thread)
            thread.start()

    def stop(self, *args, **kwargs):
        log.info("Signal set")
        self.evt.set()


class Command(BaseCommand):
    help = 'Run all background jobs'

    def handle(self, *args, **options):
        coordinator = Coordinator()
        coordinator.start()

        signal.signal(signal.SIGINT, coordinator.stop)
        signal.signal(signal.SIGTERM, coordinator.stop)

        for interval, job in find_jobs():
            coordinator.add(interval, job)

        coordinator.join()
