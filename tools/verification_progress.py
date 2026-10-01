"""Bounded Windows sharing-lock recovery for durable verification progress."""
import time


def replace_progress(temporary, destination):
    for attempt in range(10):
        try:
            temporary.replace(destination)
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 9:
                raise
            time.sleep(.01)
