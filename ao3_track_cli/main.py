from pathlib import Path
from os import makedirs
from enum import Enum
import os
import logging

import AO3
import typer
import questionary

from ao3_helpers import (
    write_human_readable_work_info,
    chapter_text_for_humans,
    get_work_id_from_user,
)
from track_metadata import MetadataFile, MetadataFileParseError
from track_helpers import work_folder_to_name, work_folder_to_id, sanitize_path
from constants import DATETIME_FORMAT


DOWNLOAD_DIR = Path(__file__).parents[1] / "downloaded_works"
INTERRUPT_MSG = "Action cancelled by KeyboardInterrupt"

app = typer.Typer()
logger = logging.getLogger(__name__)


def update_ao3_work(work: AO3.Work, always_update=False):
    """Update an AO3 work if necessary

    Args:
        work (AO3.Work): AO3 work to update
        always_update (bool, optional): Whether to update even if there have been no edits since last update. Defaults to False.
    """
    # print(f"Chapters: {len(work.chapters)}")
    work_dir = DOWNLOAD_DIR / (sanitize_path(work.title) + " " + str(work.id))
    chapters_dir = work_dir / "Chapters"
    makedirs(work_dir, exist_ok=True)

    # Check to see if anything's changed
    try:
        work_metadata = MetadataFile.read_from_work_dir(work_dir)
    except MetadataFileParseError:
        print("Invalid metadata file, overwriting...")
    except FileNotFoundError:
        print(f"Adding new work {work.title}")
    else:
        if not work_metadata.needs_updated(work):
            if always_update:
                logger.info("Doing a redundant update because always_update = True")
            else:
                print(f"{work.title} is already up to date, skipping")
                return
        else:
            new_chapters = work.nchapters - work_metadata.chapters_published
            print(
                f"Updating {work.title} ({new_chapters} new chapter{'s' if new_chapters != 1 else ''})"
            )

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


def mark_work_read(work_path: Path):
    work_info = MetadataFile.read_from_work_dir(work_path)
    try:
        chapters_read = questionary.text(
            "What chapter have you read up to?",
            validate=lambda x: x.isdigit()
            and int(x) >= 0
            and int(x) <= work_info.chapters_published,
            default=str(work_info.chapters_published),
        ).unsafe_ask()
    except KeyboardInterrupt:
        print(INTERRUPT_MSG)
        return
    work_info.chapters_read = int(chapters_read)
    work_info.write_to_work_dir(work_path)
    print("Set read chapter count!")


@app.command()
def run():
    while True:
        main()


def main():
    print("\n  Downloaded Works:")
    # print a list of all works
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    all_works = [Path(x) for x in os.scandir(DOWNLOAD_DIR) if x.is_dir()]
    if len(all_works) == 0:
        print("  There's nothing here.")
    for index, folder_path in enumerate(all_works):
        work_name = work_folder_to_name(folder_path.name)
        try:
            work_info = MetadataFile.read_from_work_dir(folder_path)
        except (MetadataFileParseError, FileNotFoundError):
            logger.warning(
                f"Skipping work {work_name} due to invalid parse file (update to fix)"
            )
            continue
        print(
            f"  {index} - {work_name} - ({work_info.chapter_count_str}){' (stale)' if work_info.is_stale else ''}"
        )
    print("")

    # what do you want to do?
    selected_app_action = questionary.select(
        "Main Menu! What's the move?",
        choices=[act.value for act in AppAction],
    ).unsafe_ask()  # don't handle interrupt
    selected_app_action = AppAction(selected_app_action)
    match selected_app_action:
        case AppAction.ADDNEWWORK:
            work_id = get_work_id_from_user()
            work = AO3.Work(work_id, load_chapters=False)
            update_ao3_work(work)
        case AppAction.UPDATEALL:
            for index, folder_path in enumerate(all_works):
                work_id = work_folder_to_id(folder_path.name)
                work = AO3.Work(work_id, load_chapters=False)
                update_ao3_work(work)
        case AppAction.SELECTWORK:
            select_work_and_act(all_works)
        case AppAction.EXIT:
            exit(0)
        case _:
            logger.error("not implemented")


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

    # now take action on the selected work
    try:
        selected_work_action = questionary.select(
            "What do you want to do with this work?",
            choices=[act.value for act in WorkAction],
        ).unsafe_ask()
    except KeyboardInterrupt:
        print(INTERRUPT_MSG)
        return
    selected_work_action = WorkAction(selected_work_action)
    match selected_work_action:
        case WorkAction.MARKREAD:
            mark_work_read(Path(selected_work))
        case WorkAction.UPDATE:
            work_id = work_folder_to_id(selected_work.name)
            work = AO3.Work(work_id, load_chapters=False)
            update_ao3_work(work)
        case _:
            logger.error("not implemented")


class AppAction(Enum):
    # action to take at the top level
    ADDNEWWORK = "Add new work"
    UPDATEALL = "Update all works"
    SELECTWORK = "Select a work"
    EXIT = "Exit"


class WorkAction(Enum):
    # action to take on an individual work
    MARKREAD = "Mark read"
    UPDATE = "Update"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app()
