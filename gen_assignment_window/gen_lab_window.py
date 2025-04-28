import os 
import re
import pytz
import tomlkit

from datetime import datetime
from csv import DictWriter
from tomlkit import document, table, comment, dumps

from CanvasRequestLibrary.main import CanvasClient

class Config:
    def __init__(self, token: str, course_id: int, assignment_name_scheme: str, generated_output_file_name: str, blacklist: list):
        self.token = token
        self.course_id= course_id
        self.assignment_name_scheme = assignment_name_scheme
        self.generated_output_file_name = generated_output_file_name
        self.client = CanvasClient(token=self.token, url_base="https://umsystem.instructure.com/api/v1/")
        self.blacklist = blacklist

class Assignment:
    def __init__(self, id: int, name: str, unlock_at: str, due_date: str):
        self.id = id
        self.name = name
        # use Unix epoch as placeholder
        self.unlock_at = "1970-01-01_00:00:00"
        if unlock_at != None:
            dt_utc = datetime.fromisoformat(unlock_at.replace("Z", "+00:00"))

            # Set the datetime object to UTC timezone
            dt_utc = dt_utc.replace(tzinfo=pytz.UTC)

            # Convert to CST (Central Standard Time)
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt_utc.astimezone(cst)
            self.unlock_at = dt_cst.strftime('%Y-%m-%d_%H:%M:%S')
        self.due_at = "1970-01-01_00:00:00"
        if due_date != None:
            dt_utc = datetime.fromisoformat(due_date.replace("Z", "+00:00"))

            # Set the datetime object to UTC timezone
            dt_utc = dt_utc.replace(tzinfo=pytz.UTC)

            # Convert to CST (Central Standard Time)
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt_utc.astimezone(cst)
            self.due_at = dt_cst.strftime('%Y-%m-%d_%H:%M:%S')
            
    def parse_json_into_assignments(json) -> []:
        assignments = []
        for body in json:
            assignments.append(Assignment(id=body['id'], name=body['name'], unlock_at=body['unlock_at'], due_date=body['due_at']))
        return assignments

def get_assignment_internals(config: Config) -> []:
    try:
        assignments = config.client._assignments.get_assignments_from_course(course_id=config.course_id, per_page=100)
    except Exception as e:
        print(str(e))
    assignments = Assignment.parse_json_into_assignments(assignments)
    assignments = [a for a in assignments if config.assignment_name_scheme in a.name and not any(phrase in a.name for phrase in config.blacklist)]
    for assignment in assignments:
        # remove stray characters
        # TODO: maybe provide a regex config option? 
        assignment.name = re.sub(r'[ ()]', '', assignment.name).lower()
    return assignments

def prepare_output(config: Config, assignments: []) -> None:
    with open(f"{config.generated_output_file_name}.csv", 'w', newline='') as csvfile:
        # `name` provides best flexibility for future MUCS courses
        fieldnames = ['name', 'start_date', 'end_date']
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        data = []
        for assignment in assignments:
            dict = {'name' : assignment.name, 'start_date' : assignment.unlock_at, 'end_date' : assignment.due_at}
            data.append(dict)
        writer.writerows(data)
        print(f"*** Generated {config.generated_output_file_name}.csv ***")


def prepare_toml() -> None:
    doc = document()

    canvas = table()
    canvas.add(comment("The Canvas LMS Token identifying your user session."))
    canvas.add("canvas_token", "")
    canvas.add(comment("The Canvas LMS course ID identifying your course."))
    canvas.add("canvas_course_id", 0)
    canvas.add(comment("The naming scheme of your assignments as found on your course."))
    canvas.add(comment("The script will attempt to find as many assignments that have this predicate."))
    canvas.add("canvas_assignment_name_predicate", "")
    canvas.add(comment("List any words that can be in assignments that you do not want included in the search."))
    canvas.add("canvas_assignment_phrase_blacklist", [""])
    doc['canvas'] = canvas
    general = table()
    general.add(comment("The name of the generated output. (it will be a .csv file)"))
    general.add("generated_output_file_name", "window")
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
    canvas = doc.get('canvas', {})
    return Config(
    token=canvas.get("canvas_token"), 
    course_id=canvas.get("canvas_course_id"), 
    assignment_name_scheme=canvas.get("canvas_assignment_name_predicate"), 
    generated_output_file_name=general.get("generated_output_file_name"),
    blacklist=canvas.get('canvas_assignment_phrase_blacklist'))



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


