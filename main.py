#!/usr/bin/python3
import os
import time

from recorder import ZoomRecorder

if __name__ == '__main__':
    rec = ZoomRecorder(os.environ["ZOOM_URL"])
    try:
        rec.record("output.mp4")
        time.sleep(30)
    finally:
        rec.stop()
