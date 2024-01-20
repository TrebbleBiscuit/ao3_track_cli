# ao3_track_cli

An unofficial command line tool that interacts with Archive of Our Own (AO3)
- Paste a url to add a work
- Download a work's metadata and raw text
- Track number of chapters read

### How to run

You'll need python, I'm using 3.10

Using the package
- Grab the `.whl` from the releases page
- `pip install path/to/.whl`
- `python -m ao3_track_cli`

With [poetry](https://python-poetry.org/):
- Clone this repository
- `poetry install`
- `poetry run python ao3_track_cli/main.py`

Without poetry
- Clone this repository
- `pip install ao3-api questionary typer`
- `python ao3_track_cli/main.py`

### Non-interactive mode

Running `main.py` with no arguments will run in interactive mode.

`main.py --help` will show available commands.

`main.py add-work --help` will show arguments for the `add-work` command.
