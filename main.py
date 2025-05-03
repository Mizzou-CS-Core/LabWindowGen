import logging
import os

import tomlkit

from colorlog import ColoredFormatter

from canvas_lms_api import init as initialize_canvas_client
from mucs_database.init import initialize_database

from gen_assignment_window.gen_assignment_window import Config, prepare_toml, filter_out_assignments


def setup_logging():
    handler = logging.StreamHandler()
    # this format string lets colorlog insert color around the whole line
    fmt = "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
    handler.setFormatter(ColoredFormatter(fmt, log_colors=colors))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


logger = logging.getLogger(__name__)


def load_config() -> Config:
    """
    Loads the data from a config file into memory.
    """
    with open("gen_assignment_window.toml", 'r') as f:
        content = f.read()
    doc = tomlkit.parse(content)

    # Extract values from the TOML document
    general = doc.get('general', {})
    canvas = doc.get('canvas', {})
    paths = doc.get('paths', {})
    logger.info("Loading toml to memory")
    return Config(
        token=canvas.get("canvas_token"),
        course_id=canvas.get("canvas_course_id"),
        assignment_name_scheme=canvas.get("canvas_assignment_name_predicate"),
        blacklist=canvas.get('canvas_assignment_phrase_blacklist'),
        mucs_instance_code=general.get("mucs_instance_code"),
        sqlite3_path=paths.get("sqlite3_path")
    )


def main():
    if not os.path.exists("gen_assignment_window.toml"):
        prepare_toml()
        logger.error(f"gen_assignment_window.toml was just created!")
        logger.error(f"To continue with program execution, please edit this file with your preferred values.")
        exit()
    config: Config = load_config()
    initialize_canvas_client(url_base="https://umsystem.instructure.com/api/v1/", token=config.token)
    initialize_database(sqlite_db_path=str(config.sqlite3_path), mucsv2_instance_code=config.mucs_instance_code)
    filter_out_assignments(course_id=config.course_id, assignment_name_scheme=config.assignment_name_scheme,
                           blacklist=config.blacklist)


if __name__ == "__main__":
    setup_logging()
    main()
