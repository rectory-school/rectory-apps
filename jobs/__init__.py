"""Job tracking library"""


from typing import Callable, List, Tuple, Union
from datetime import timedelta
import logging
import importlib

from django.conf import settings

Job = Callable[[], None]
RegisteredJob = Tuple[timedelta, Job]

log = logging.getLogger(__name__)

registered_items: List[RegisteredJob] = []


def schedule(interval: Union[timedelta, int, None] = None):
    """Schedule the job to be run ever interval,
    or continuiously with no interval"""

    if not interval:
        interval = timedelta(seconds=0)

    if isinstance(interval, int):
        interval = timedelta(seconds=interval)

    def decorator(func: Callable[[], None]):
        registered_items.append((interval, func))

        return func

    return decorator


def find_jobs() -> List[RegisteredJob]:
    """Iterate through all Django apps and find their jobs"""

    for app_name in settings.INSTALLED_APPS:
        try:
            module_name = f"{app_name}.jobs"
            log.info("Importing %s", module_name)

            # This will cause the decorators to be run and jobs to be registered
            importlib.import_module(module_name)
        except ImportError:
            log.debug("Package %s did not have a jobs file", app_name)

    return registered_items
