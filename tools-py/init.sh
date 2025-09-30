#!/bin/sh


# Create a python virtual environment
python3 -m venv env


# Activate the environment
source env/bin/activate
#source env/bin/activate.csh
#source env/bin/activate.fish


# Install dependencies
pip install -r requirements.txt

