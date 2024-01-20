from pathlib import Path
from os import makedirs
import os
import logging

import AO3
import questionary
import typer

from ao3_track_cli.ao3_helpers import (
    write_human_readable_work_info,
    chapter_text_for_humans,
    work_id_from_user_input,
)
from ao3_track_cli.track_metadata import MetadataFile
from ao3_track_cli.track_helpers import (
    work_folder_to_name,
    work_folder_to_id,
    sanitize_path,
    prompt_user_for_app_action,
    AppAction,
    WorkAction,
    does_work_need_updating,
    list_downloaded_works,
    mark_work_read,
)
from ao3_track_cli.constants import DATETIME_FORMAT, INTERRUPT_MSG


DOWNLOAD_DIR = Path(__file__).parents[1] / "downloaded_works"

app = typer.Typer()
logger = logging.getLogger(__name__)


def update_work(work: AO3.Work, always_update=False):
    """Check for updates to an AO3 work and update if necessary

    Args:
        work (AO3.Work): AO3 work to update
        always_update (bool, optional): Whether to update even if there have been no edits since last update. Defaults to False.
    """
    # print(f"Chapters: {len(work.chapters)}")
    work_dir = DOWNLOAD_DIR / (sanitize_path(work.title) + " " + str(work.id))
    chapters_dir = work_dir / "Chapters"
    makedirs(work_dir, exist_ok=True)

    # Check to see if anything's changed
    if not does_work_need_updating(work, work_dir):
        return

    # Write work info
    write_human_readable_work_info(work, work_dir / "_INFO.txt")

    # Write all chapters to file
    work.load_chapters()
    makedirs(chapters_dir, exist_ok=True)
    for chapter in work.chapters:
        assert chapter.loaded
        with open(
            chapters_dir / f"Chapter {chapter.number}.txt", "w", encoding="utf-8"
        ) as chapterfile:
            chapterfile.write(chapter_text_for_humans(chapter))

    # Write end notes
    if work.end_notes:
        with open(work_dir / "END_NOTES.txt", "w", encoding="utf-8") as endnotesfile:
            endnotesfile.write(work.end_notes)

    # Write update file
    update_file = MetadataFile(
        date_updated=work.date_updated.strftime(DATETIME_FORMAT),
        work_id=work.id,
        chapters_published=work.nchapters,
        chapters_expected=work.expected_chapters,
    )
    update_file.write_to_work_dir(work_dir=work_dir)


def select_work_and_act(all_works: list[Path]):
    # ask the user to select a work
    try:
        selected_index = questionary.text(
            "Please select a work by number.",
            validate=lambda x: x.isdigit() and int(x) >= 0 and int(x) < len(all_works),
        ).unsafe_ask()
    except KeyboardInterrupt:
        print(INTERRUPT_MSG)
        return
    selected_index = int(selected_index)
    selected_work = all_works[selected_index]
    # confirmation is nice to have
    print(f"You selected: {work_folder_to_name(selected_work.name)} \n")

    # have user select what they want to do with this work
    try:
        selected_work_action = questionary.select(
            "What do you want to do with this work?",
            choices=[act.value for act in WorkAction],
        ).unsafe_ask()
        selected_work_action = WorkAction(selected_work_action)
    except KeyboardInterrupt:
        print(INTERRUPT_MSG)
        return
    # then actually do it
    match selected_work_action:
        case WorkAction.MARKREAD:
            mark_work_read(Path(selected_work))
        case WorkAction.UPDATE:
            work_id = work_folder_to_id(selected_work.name)
            work = AO3.Work(work_id, load_chapters=False)
            update_work(work)
        case _:
            logger.error("not implemented")


def interactive_mode():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    while True:
        # print a list of all works
        all_works = [Path(x) for x in os.scandir(DOWNLOAD_DIR) if x.is_dir()]
        list_downloaded_works(all_works)

        # what do you want to do?
        selected_app_action = prompt_user_for_app_action()
        match selected_app_action:
            case AppAction.ADDNEWWORK:
                new_work_from_user = questionary.text(
                    "Please enter the work's URL or ID.",
                    validate=lambda x: bool(x),
                ).unsafe_ask()
                add_work(new_work_from_user)
            case AppAction.UPDATEALL:
                update_all()
            case AppAction.SELECTWORK:
                select_work_and_act(all_works)
            case AppAction.EXIT:
                exit(0)
            case _:
                logger.error("not implemented")


@app.command()
def update_all():
    """Update all downloaded works"""
    all_works = [Path(x) for x in os.scandir(DOWNLOAD_DIR) if x.is_dir()]
    for folder_path in all_works:
        work_id = work_folder_to_id(folder_path.name)
        work = AO3.Work(work_id, load_chapters=False)
        update_work(work)


@app.command()
def add_work(work_id_or_url: str):
    """Add a new AO3 work given its ID or URL

    Args:
        work_id_or_url (str)
    """
    work_id = work_id_from_user_input(work_id_or_url)
    work = AO3.Work(work_id, load_chapters=False)
    update_work(work)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """AO3 track cli will run in interactive mode if no commands are provided"""
    # this will ALWAYS be run which is why we do this check
    if ctx.invoked_subcommand is None:
        interactive_mode()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
