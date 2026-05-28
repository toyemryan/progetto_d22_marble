import threading
import itertools
import time

def spinner(stop_event: threading.Event, message: str = "") -> None:
    start = time.time()
    for frame in itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]):
        if stop_event.is_set():
            break
        elapsed = int(time.time() - start)
        print(f"\r{message} {frame} {elapsed}s", end="", flush=True)
        time.sleep(0.1)
    print("\r" + " " * 50 + "\r", end="", flush=True)  # pulizia riga