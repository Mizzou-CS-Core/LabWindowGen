import getpass
import sys
import os 
import re
import shutil
import signal
import stat
from datetime import datetime
from pathlib import Path

from CanvasRequestLibrary.main import CanvasClient

import tomlkit
from tomlkit import document, table, comment, dumps


# https://pypi.org/project/colorama/


from csv import DictReader
from subprocess import DEVNULL, PIPE, run

class Config:
    def __init__(self, token: str, course_id: int, assignment_name_scheme: str, internal_mucs_name: str):
        self.token = token
        self.course_id= course_id
        self.assignment_name_scheme = assignment_name_scheme
        self.internal_mucs_name = internal_mucs_name
        self.client = CanvasClient(token=self.token, url_base="https://umsystem.instructure.com/api/v1/")


def generate_window_file(config: Config) -> None:
    try:
        assignments = config.client._assignments.get_assignments_from_course(course_id=config.course_id)
        print(assignments)
    except Exception as e:
        print(str(e))


def prepare_toml() -> None:
    doc = document()

    general = table()
    general.add(comment("The Canvas LMS Token identifying your user session."))
    general.add("canvas_token", "")
    general.add(comment("The Canvas LMS course ID identifying your course."))
    general.add("canvas_course_id", 0)
    general.add(comment("The naming scheme of your assignments as found on your course."))
    general.add(comment("The script will attempt to find as many assignments that have this predicate."))
    general.add("canvas_assignment_name_predicate", "")
    general.add(comment("The MUCS internal name for each assignment."))
    general.add(comment("In general, you can expect this to be like \"lab1, lab2, ... labx\" "))
    general.add("internal_mucs_name", "")
    doc['general'] = general

    with open("config.toml", 'w') as f:
        f.write(dumps(doc))
    print("Created default toml config")
def load_config() -> Config:
    with open("config.toml", 'r') as f:
        content = f.read()
    doc = tomlkit.parse(content)

    # Extract values from the TOML document
    general = doc.get('general', {})
    return Config(
    token=general.get("canvas_token"), 
    course_id=general.get("canvas_course_id"), 
    assignment_name_scheme=general.get("canvas_assignment_name_predicate"), 
    internal_mucs_name=general.get("internal_mucs_name"))



def main():
    if not os.path.exists("config.toml"):
        prepare_toml()
    config = load_config()
    generate_window_file(config=config)

if __name__ == "__main__":
    main()


