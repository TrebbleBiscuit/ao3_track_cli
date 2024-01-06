# ao3_track_cli

An unofficial command line tool that interacts with Archive of Our Own (AO3)
- Paste a url to add a work
- Download a work's metadata and raw text
- Track number of chapters read

### How to run

You'll need python, I'm using 3.10

With [poetry](https://python-poetry.org/):

- `poetry install`
- `poetry run python ao3_track_cli/main.py`

Without poetry

- `pip install ao3-api questionary typer`
- `python ao3_track_cli/main.py`
