@echo off

REM Transformation des fichiers Qt Designer en classes Python

pyuic5 mainwindow.ui > mainwindow.py
pyuic5 species_params.ui > species_params.py
pyuic5 create_model.ui > create_model.py
pyuic5 edit_model.ui > edit_model.py