from typing import Any


import getpass
import sys
import os 
import re
import shutil
import signal
import stat
from datetime import datetime
from pathlib import Path

from CanvasRequestLibrary.request import canvas_api_call


# https://pypi.org/project/colorama/


from csv import DictReader
from subprocess import DEVNULL, PIPE, run


def generate_window_file(token: str, course_canvas_id: int) -> None:
    try:
        response = canvas_api_call(endpoint=f"{course_canvas_id}/assignments", token=token)
    except Exception as e:
        print(str(e))





