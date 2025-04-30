import os 
import re
import pytz
import tomlkit
import sqlite3
import logging

from datetime import datetime
from csv import DictWriter
from tomlkit import document, table, comment, dumps

from canvas_lms_api import CanvasClient, Assignment

logger = logging.getLogger(__name__).addHandler(logging.NullHandler())


class Config:
    def __init__(self, token: str, course_id: int, assignment_name_scheme: str, generated_output_file_name: str, blacklist: list, mucs_course_code):
        self.token = token
        self.course_id= course_id
        self.assignment_name_scheme = assignment_name_scheme
        self.client = CanvasClient(token=self.token, url_base="https://umsystem.instructure.com/api/v1/")
        self.blacklist = blacklist
        self.mucs_course_code = mucs_course_code

def get_assignment_internals(config: Config) -> []:
    logger.info("gen_assignment_window$get_assignment_internals: Retrieving assignments from Canvas LMS")
    try:
        assignments = config.client._assignments.get_assignments_from_course(course_id=config.course_id, per_page=100)
    except Exception as e:
        logger.error(f"gen_assignment_window$get_assignment_internals: Failed to get assignments: {e}")
    logger.info(f"gen_assignment_window$get_assignment_internals: Assignment count from Canvas LMS: {len(assignments)}")
    assignments = [a for a in assignments if config.assignment_name_scheme in a.name and not any(phrase in a.name for phrase in config.blacklist)]
    for assignment in assignments:
        # remove stray characters
        # TODO: maybe provide a regex config option? 
        assignment.name = re.sub(r'[ ()]', '', assignment.name).lower()
        logger.info(f"gen_assignment_window$get_assignment_internals: Internal assignment name {assignment.name} assigned")
    return assignments

def prepare_output(config: Config, assignments: [], cursor: Cursor) -> None:
    sql = "INSERT INTO assignments(canvas_id, mucs_course_code, name, open_at, due_at) VALUES (?, ?, ?, ?, ?)"
    for assignment in assignments:
        asn = (assignment.id, config.mucs_course_code, assignment.name, assignment.unlock_at, assignment.due_at)
        logger.info(f"gen_assignment_window$prepare_output: Inserting {asn}")
        try:
            cursor.execute(sql, asn)
        except sqlite3.Exception as e:
            logger.error(f"gen_assignment_window$prepare_output: Failed to insert row {asn}: {e}")
    cursor.commit()

def prepare_toml(config_path = Path(""), canvas_token = 0, canvas_course_id = 0, canvas_assignment_name_predicate = "", canvas_assignment_phrase_blacklist = [""], mucs_course_code = "") -> None:
    doc = document()
    general = table()
    general.add("mucs_course_code", mucs_course_code)
    doc['general']
    canvas = table()
    canvas.add(comment("The Canvas LMS Token identifying your user session."))
    canvas.add("canvas_token", canvas_token)
    canvas.add(comment("The Canvas LMS course ID identifying your course."))
    canvas.add("canvas_course_id", canvas_course_id)
    canvas.add(comment("The naming scheme of your assignments as found on your course."))
    canvas.add(comment("The script will attempt to find as many assignments that have this predicate."))
    canvas.add("canvas_assignment_name_predicate", canvas_assignment_name_predicate)
    canvas.add(comment("List any words that can be in assignments that you do not want included in the search."))
    canvas.add("canvas_assignment_phrase_blacklist", canvas_assignment_phrase_blacklist)
    doc['canvas'] = canvas

    with open(config_path / "gen_lab_window_config.toml", 'w') as f:
        f.write(dumps(doc))
    print("Created default toml config")
def load_config() -> Config:
    with open("gen_lab_window_config.toml", 'r') as f:
        content = f.read()
    doc = tomlkit.parse(content)

    # Extract values from the TOML document
    general = doc.get('general', {})
    canvas = doc.get('canvas', {})
    return Config(
    token=canvas.get("canvas_token"), 
    course_id=canvas.get("canvas_course_id"), 
    assignment_name_scheme=canvas.get("canvas_assignment_name_predicate"), 
    generated_output_file_name=general.get("generated_output_file_name"),
    blacklist=canvas.get('canvas_assignment_phrase_blacklist'),
    mucs_course_code=general.get("mucs_course_code")
    )


def initialize_window(cursor: Cursor, config_path = Path(""), canvas_token = 0, canvas_course_id = 0, canvas_assignment_name_predicate = "", canvas_assignment_phrase_blacklist = [""], mucs_course_code = ""):
    prepare_toml(config_path = config_path, canvas_token = canvas_token, canvas_course_id = canvas_course_id, canvas_assignment_name_predicate = canvas_assignment_name_predicate, canvas_assignment_phrase_blacklist = canvas_assignment_phrase_blacklist, mucs_course_code=mucs_course_code)
    logger.info(f"gen_assignment_window$initialize_window: Creating default TOML using config_path: {config_path}, canvas_token=REDACTED, canvas_course_id={canvas_course_id}, canvas_assignment_name_predicate={canvas_assignment_name_predicate}, canvas_assignment_phrase_blacklist={canvas_assignment_phrase_blacklist}, mucs_course_code={mucs_course_code}")
    config = Config(token=canvas_token, course_id=canvas_course_id, assignment_name_scheme=canvas_assignment_name_predicate, blacklist=canvas_assignment_phrase_blacklist, mucs_course_code=mucs_course_code)
    assignments = get_assignment_internals(config=config)
    logger.info(f"gen_assignment_window$initialize_window: Retrieved assignments: count of {len(assignments)}")

def main():
    if not os.path.exists("config.toml"):
        prepare_toml()
        exit()
    print("*** This isn't perfect - you should double check the results to make sure you're happy with them. ***")
    config: Config = load_config()
    assignments: [] = get_assignment_internals(config=config)
    prepare_output(config=config, assignments=assignments)

if __name__ == "__main__":
    main()


