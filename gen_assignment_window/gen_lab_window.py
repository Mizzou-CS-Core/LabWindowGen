import os 
import re
import tomlkit
import sqlite3
import logging
from pathlib import Path


from datetime import datetime
from csv import DictWriter
from tomlkit import document, table, comment, dumps

from canvas_lms_api import get_client, Assignment
import mucs_database.store_objects as dao

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Config:
    def __init__(self, token: str, course_id: int, assignment_name_scheme: str, blacklist: list, mucs_course_code):
        self.token = token
        self.course_id= course_id
        self.assignment_name_scheme = assignment_name_scheme
        self.blacklist = blacklist

def get_assignment_internals(config: Config) -> []:
    logger.debug("$get_assignment_internals: Retrieving assignments from Canvas LMS")
    try:
        assignments = get_client()._assignments.get_assignments_from_course(course_id=config.course_id, per_page=100)
    except Exception as e:
        logger.error(f"$get_assignment_internals: Failed to get assignments: {e}")
    logger.debug(f"$get_assignment_internals: Assignment count from Canvas LMS: {len(assignments)}")
    assignments = [a for a in assignments if config.assignment_name_scheme in a.name and not any(phrase in a.name for phrase in config.blacklist)]
    for assignment in assignments:
        # remove stray characters
        # TODO: maybe provide a regex config option? 
        assignment.name = re.sub(r'[ ()]', '', assignment.name).lower()
        logger.debug(f"$get_assignment_internals: Internal assignment name {assignment.name} assigned")
        dao.store_assignment(assignment=assignment)

# Accepts values to prepare a "partial" configuration if necessary
def prepare_toml(config_path = Path(""), canvas_token = "", canvas_course_id = 0, canvas_assignment_name_predicate = "", canvas_assignment_phrase_blacklist = [""], mucs_course_code = "") -> None:
    if canvas_token != "":
        logger.info("$prepare_toml: Creating gen_lab_window_config.toml with pre-provided defaults")
    else:
        logger.info("$prepare_toml: Creating gen_lab_window_config.toml with empty defaults")
    doc = document()
    general = table()
    general.add("mucs_course_code", mucs_course_code)
    doc['general'] = general
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
    logger.info("$prepare_toml: Created toml config")

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


def prepare_assignment_window_and_config(config_path = Path(""), canvas_token = 0, canvas_course_id = 0, canvas_assignment_name_predicate = "", canvas_assignment_phrase_blacklist = [""], mucs_course_code = ""):
    prepare_toml(config_path = config_path, canvas_token = canvas_token, canvas_course_id = canvas_course_id, canvas_assignment_name_predicate = canvas_assignment_name_predicate, canvas_assignment_phrase_blacklist = canvas_assignment_phrase_blacklist, mucs_course_code=mucs_course_code)
    logger.info("Created default TOML configuration for gen_assignment_window")
    config = Config(token=canvas_token, course_id=canvas_course_id, assignment_name_scheme=canvas_assignment_name_predicate, blacklist=canvas_assignment_phrase_blacklist, mucs_course_code=mucs_course_code)
    get_assignment_internals(config=config)

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


