import threading
from utils.spinner import spinner

def call_with_spinner(function, *args, label="Loading...", **kwargs):
    """
    Calls a function with a spinner loader and returns its result.
    """
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=spinner, args=(stop_event, label))
    spinner_thread.start()

    try:
        result = function(*args, **kwargs)
    finally:
        stop_event.set()
        spinner_thread.join()

    return result