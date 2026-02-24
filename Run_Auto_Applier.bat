@echo off
title JobStreet Auto-Applier
color 0A

:: Switch to the directory where this batch script is located
cd /d "%~dp0"

echo ===================================================
echo             JobStreet Auto-Applier Script
echo ===================================================
echo.
echo Starting the Python automation...
echo.

:: Run the python script
python automaton\apply_jobs.py

echo.
echo ===================================================
echo Script execution finished or was stopped.
echo ===================================================
pause
