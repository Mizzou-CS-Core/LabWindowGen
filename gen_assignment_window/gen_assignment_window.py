import logging
import re
from pathlib import Path

import mucs_database.assignment.accessors as dao_assignments
from colorama import Fore, Style
from canvas_lms_api import get_client
from tomlkit import document, table, comment, dumps

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Config:
    def __init__(self, token: str, course_id: int, assignment_name_scheme: str, blacklist: list,
                 mucs_instance_code: str, sqlite3_path: str):
        self.token = token
        self.course_id = course_id
        self.assignment_name_scheme = assignment_name_scheme
        self.blacklist = blacklist
        self.mucs_instance_code = mucs_instance_code
        self.sqlite3_path = Path(sqlite3_path)


def filter_out_assignments(course_id: int, assignment_name_scheme: str, blacklist: list):
    """
    Retrieves the assignments from a course, filters their name based on the given predicate and blacklist,
    and stores it to the MUCS db.
    :param course_id: The ID of the course to retrieve assignments from.
    :param assignment_name_scheme: the pattern to match in Canvas assignments
    :param blacklist: phrases which should not appear in MUCSv2 assignments from Canvas
    """
    global_type = None
    global_count = None
    logger.debug(f"${filter_out_assignments.__name__}: Retrieving assignments from Canvas LMS")
    try:
        assignments = get_client().assignments.get_assignments_from_course(course_id, per_page=100)
    except Exception as e:
        logger.error(f"${filter_out_assignments.__name__}: Failed to get assignments: {e}")
        return
    logger.debug(f"${filter_out_assignments.__name__}: Assignment count from Canvas LMS: {len(assignments)}")
    assignments = [a for a in assignments if
                   assignment_name_scheme in a.name and not any(phrase in a.name for phrase in blacklist)]
    for assignment in assignments:
        if global_type is None:
            control = False
            while (not control):
                assignment_type = input(f"{Fore.BLUE}What kind of assignment is this? Valid options: c, cpp, none \nYou can put * at the end to mark all assignments as the same type.\n> {Style.RESET_ALL}")
                if "c" in assignment_type or "cpp" in assignment_type or "none" in assignment_type:
                    control = True
            if "*" in assignment_type:
                assignment_type = assignment_type.translate({ord(i):None for i in '*'})
                global_type = assignment_type
                print(f"{Fore.BLUE}All assignments will now be {assignment_type} type.{Style.RESET_ALL}")
        else:
            assignment_type = global_type
        control = False
        if global_count is None:
            file_count = input(f"{Fore.BLUE}How many files should be expected with the submission? \nYou can put * at the end to mark all assignments as the same type.\n> {Style.RESET_ALL}")
            if "*" in file_count:
                file_count = file_count.translate({ord(i):None for i in '*'})
                global_count = file_count
                print(f"{Fore.BLUE}All assignments will now need {file_count} files.{Style.RESET_ALL}")
        else:
            file_count = global_count

        original_name = assignment.name
        # remove stray characters
        # TODO: maybe provide a regex config option? 
        assignment.name = re.sub(r'[ ()]', '', assignment.name).lower()
        logger.debug(f"${filter_out_assignments.__name__}: Internal assignment name {assignment.name} assigned")
        result = dao_assignments.store_assignment(name=assignment.name, canvas_id=assignment.id,
                                                  open_at=assignment.unlock_at, due_at=assignment.due_at, 
                                                  original_name=original_name, assignment_type=assignment_type, file_count=file_count)
        logger.info(f"Added {result} to DB")
        if result is None:
            logger.error(f"Failed to add {assignment.name} to DB")


# Accepts values to prepare a "partial" configuration if necessary
def prepare_toml(config_path: Path = Path(""), canvas_token: str = "", canvas_course_id: int = 0,
                 canvas_assignment_name_predicate: str = "", canvas_assignment_phrase_blacklist=None,
                 mucs_instance_code: str = "", sqlite3_path: str = "") -> None:
    """
    Generates a configuration toml for future use. Accepts optional values to form a partial configuration default.
    :param config_path: location of configuration file
    :param canvas_token: token from Canvas LMS for API calls
    :param canvas_course_id: Canvas course IDs associated with the MUCSv2 instance.
    :param canvas_assignment_name_predicate: the pattern to match in Canvas assignments
    :param canvas_assignment_phrase_blacklist: phrases which should not appear in MUCSv2 assignments from Canvas
    :param mucs_instance_code: The code of the MUCSv2 instance you're using :param
    :param sqlite3_path: Path to the MUCSv2 Database
    """

    if canvas_assignment_phrase_blacklist is None:
        canvas_assignment_phrase_blacklist = [""]
    if canvas_token != "":
        logger.debug(f"${prepare_toml.__name__}: Creating gen_lab_window_config.toml with pre-provided defaults")
    else:
        logger.debug(f"${prepare_toml.__name__}: Creating gen_lab_window_config.toml with empty defaults")
    doc = document()
    general = table()
    general.add("mucs_instance_code", mucs_instance_code)
    doc['general'] = general
    paths = table()
    paths.add("sqlite3_path", sqlite3_path)
    doc['paths'] = paths
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

    with open(config_path / "gen_assignment_window.toml", 'w') as f:
        f.write(dumps(doc))
    logger.debug(f"${prepare_toml.__name__}: Created toml config")


def prepare_assignment_window(canvas_course_id: int = 0, canvas_assignment_name_predicate: str = "",
                              canvas_assignment_phrase_blacklist=None):
    """
    Prepares the assignments of an MUCSv2 instance.

    :param canvas_course_id: Canvas course ID to prepare assignments from.
    :param canvas_assignment_name_predicate: the pattern to match in Canvas assignments
    :param canvas_assignment_phrase_blacklist: phrases which should not appear in MUCSv2 assignments from Canvas
    """
    if canvas_assignment_phrase_blacklist is None:
        logger.debug(f"${prepare_assignment_window.__name__}: Blacklist was empty. using empty default")
        canvas_assignment_phrase_blacklist = [""]
    filter_out_assignments(course_id=canvas_course_id, blacklist=canvas_assignment_phrase_blacklist,
                           assignment_name_scheme=canvas_assignment_name_predicate)
