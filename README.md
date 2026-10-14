# Library Book Management System

A Python desktop app for managing a small library. Its Tkinter interface tracks books, borrowers, loans, due dates, returns, and overdue items. SQLite stores records locally, and reports create charts.

## Features

- Add books with title, author, category, optional ISBN, and copy count.
- Search the catalogue by title, author, or ISBN.
- Issue books to borrowers with due dates.
- Record returns and update available copies.
- Highlight overdue loans and prevent deleting books currently on loan.
- Save records in a local SQLite database and generate report images.

## Requirements

- Python 3.10 or newer
- Tkinter (included with most Windows Python installations)
- Packages listed in requirements.txt

## Run on Windows

Open Command Prompt in the project folder and run:

    py -m venv .venv
    .venv\Scripts\activate
    py -m pip install -r requirements.txt
    py main.py

If py is unavailable, use python instead.

## Project files

- main.py — Tkinter interface and library operations.
- analysis.py — creates report charts.
- requirements.txt — Python package dependencies.
- output_images/ — generated chart images.
- library.db — local database created automatically when the app runs.

## Data and backup

The database is stored beside the application. Close the app before copying library.db to make a backup. Keep this file to preserve saved records.

## Deployment

This is a Tkinter desktop application. GitHub stores and shares its source code, but GitHub Pages cannot run its interactive desktop window. To distribute it for Windows, package it with PyInstaller:

    py -m pip install pyinstaller
    pyinstaller --onefile --windowed --name LibraryManager main.py

For an interactive website, the interface must be adapted to a web framework such as Flask or Streamlit.
