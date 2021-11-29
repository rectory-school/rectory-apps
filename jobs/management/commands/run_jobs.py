from typing import List
from threading import Thread, Event, Lock

import logging
from datetime import datetime, timedelta
import signal
from random import random

from django.core.management.base import BaseCommand

from jobs import find_jobs, RegisteredJob

log = logging.getLogger(__name__)


class JobThread(Thread):
    def __init__(self, job: RegisteredJob):
        self.job = job

        self._stopping = Event()

        super().__init__()

    def run(self):
        log.info("Thread for %s executing every %s + %s started", self.job.name, self.job.interval, self.job.variance)

        while not self._stopping.is_set():
            log.info("Starting %s", self.job.name)
            started_at = datetime.now()

            try:
                self.job.func()
                log.info("Finished %s successfully", self.job.name)
            except Exception as exc:
                log.exception("Finished %s with exception: %s", self.job.name, exc)

            this_interval = self.job.interval + random() * self.job.variance
            next_run = started_at + this_interval
            now = datetime.now()
            delay = next_run - now

            if delay.total_seconds() > 0:
                log.info("%s not ready to be run, waiting %s", self.job.name, delay)

                # We do the delay inside of the event wait so that we can respond
                # immediatly to a stop signal. If we get a stop signal, we'll
                # stop the wait here and then immediatly exit the while loop
                self._stopping.wait(delay.total_seconds())
            else:
                log.info("%s being run with no delay", self.job.name)

        log.info("Thread running %s stopped", self.job.name)

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
            log.info("Waiting for %s shutdown", worker.job.name)
            worker.join()
            log.info("%s shutdown finished", worker.job.name)

        log.info("Job tracker thread finished")

    def add(self, job: RegisteredJob):
        with self._lock:
            thread = JobThread(job)
            self.workers.append(thread)
            thread.start()

    def stop_signal(self, *args, **kwargs):
        log.info("Signal set")
        self.evt.set()


class Command(BaseCommand):
    help = 'Run all background jobs'

    def handle(self, *args, **options):
        coordinator = Coordinator()
        coordinator.start()

        signal.signal(signal.SIGINT, coordinator.stop_signal)
        signal.signal(signal.SIGTERM, coordinator.stop_signal)

        for job in find_jobs():
            coordinator.add(job)

        coordinator.join()
