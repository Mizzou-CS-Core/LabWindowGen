# LabWindowGen





This project generates a MUCS-v2 compatible assignment lookup table from an associated Canvas course. 

On an initial run, you will be asked to configure a .toml file with your Canvas information and your parameters. 

Currently, mucsmake relies on this data to ensure that the assignment/lab is submitted on time. 




# Set Up

*Many of these set up steps are performed automatically if you have initialized your MUCSv2 course instance correctly using https://github.com/Mizzou-CS-Core/MUCS_Startup*. 




A Python 3.7+ interpreter is required. It is recommended that you create a Python virtual environment for using this application.
There are some required modules in MUCSMake. You can install them with `pip install -r requirements.txt`. 

To configure runtime properties, first run the program at least once. This will create an editable `config.toml` document that you can edit with your specifications. You will need to specify a database file path and the MUCSv2 instance code associated with your MUCSv2 instance. 

For each assignment, you should have a directory corresponding to the name in `data/test_files` of your MUCSv2 instance. (This is done automatically during MUCSv2 initialization). You will need to place the C source code, headers, and optionally Makefiles corresponding to the assignment. (MUCSMake will detect if the assignment uses a Makefile.)
