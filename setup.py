from setuptools import setup, find_packages

setup(
  name="gen_assignment_window",
  version="0.3.7",
  packages=find_packages(include=["gen_assignment_window", "gen_assignment_window.*"]),
  install_requires=[
  "canvas_lms_api @ git+https://github.com/Mizzou-CS-Core/CanvasRequestLibrary.git#egg=canvas_lms_api",
  ],
)