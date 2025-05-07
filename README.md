# LabWindowGen


This project is a set of wrappers and abstractions for adding Canvas assignment data to a MUCSv2 course instance.

It is available as both a standalone application, and as an editable pip module in use in other projects. 

It is dependent on [canvas_lms_api](https://github.com/Mizzou-CS-Core/CanvasRequestLibrary) and [mucs_database](https://github.com/Mizzou-CS-Core/MUCSDao).

Other projects in the MUCSv2 family of applications use this library, including [MUCS_Startup](https://github.com/Mizzou-CS-Core/MUCS_Startup).



## Set Up for Standalone Application

*Many of these set up steps are performed automatically if you have initialized your MUCSv2 course instance correctly using https://github.com/Mizzou-CS-Core/MUCS_Startup*. 


A Python 3.7+ interpreter is required. It is recommended that you create a Python virtual environment for using this application.
There are some required modules in MUCSMake. You can install them with `pip install -r requirements.txt`. 

To configure runtime properties, first run the program at least once. This will create an editable `config.toml` document that you can edit with your specifications. You will need to specify a database file path and the MUCSv2 instance code associated with your MUCSv2 instance. 

## Set Up as Pip Library

For best results, you should use `piptools`. Add the GitHub Repo as an HTTPS URL along with `#egg-info=gen_assignment_window` to a `requirements.in`. Then compile it using `pip-compile requirements.in`. This will generate a `requirements.txt` with the appropriate URL for downloading. 

## Usage

The standalone application can be run as `python3 main.py`. 

The `config.toml` should be configured with the Canvas course ID you're loading into MUCSv2, as well as your `canvas_assignment_name_predicate`. This value defines a keyword that a target assignment must include in its' name order to be included in the MUCSv2 instance. You can also define keywords in `canvas_assignment_phrase_blacklist`, which an assignment **must not** include in its' name. 

On runtime, you'll be asked to define 1. what language your assignment is focused on (currently supporting `c`, `cpp`, or `none`) and 2. how many files should be expected as part of a submission to that assignment. If you know that all of your assignments will be the same, you can input an asterisk `*` at the end of your inputs to tell the program to stop asking. 

Assignment names will be formatted down to all lowercase, only alphanumeric characters, and no whitespace. For example, an assignment name like "Lab 12" will get formatted to `lab12`. 


