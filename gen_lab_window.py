import getpass
import sys
import os 
import re
import shutil
import signal
import stat
import pytz
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

class Assignment:
    def __init__(self, id: int, name: str, unlock_at: str, due_date: str):
        self.id = id
        self.name = name
        self.unlock_at = None
        if unlock_at != None:
            dt_utc = datetime.fromisoformat(unlock_at.replace("Z", "+00:00"))

            # Set the datetime object to UTC timezone
            dt_utc = dt_utc.replace(tzinfo=pytz.UTC)

            # Convert to CST (Central Standard Time)
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt_utc.astimezone(cst)

            self.open_date: datetime = dt_cst
        self.due_at = None
        if due_date != None:
            dt_utc = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

            # Set the datetime object to UTC timezone
            dt_utc = dt_utc.replace(tzinfo=pytz.UTC)

            # Convert to CST (Central Standard Time)
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt_utc.astimezone(cst)
            self.due_at: datetime = dt_cst
    def parse_json_into_assignments(json) -> []:
        assignments = []
        for body in json:
            assignments.append(Assignment(id=body['id'], name=body['name'], unlock_at=body['unlock_at'], due_date=body['due_at']))
        return assignments

def generate_window_file(config: Config) -> None:
    try:
        assignments = config.client._assignments.get_assignments_from_course(course_id=config.course_id, per_page=100)
    except Exception as e:
        print(str(e))
    assignments = Assignment.parse_json_into_assignments(assignments)
    

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


