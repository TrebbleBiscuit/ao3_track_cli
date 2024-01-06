import re
from enum import Enum
from pathlib import Path
import logging

import AO3
import questionary

from track_metadata import MetadataFile, MetadataFileParseError
from constants import INTERRUPT_MSG

logger = logging.getLogger(__name__)


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


def prompt_user_for_app_action():
    try:
        selected_app_action = questionary.select(
            "Main Menu! What's the move?",
            choices=[act.value for act in AppAction],
        ).unsafe_ask()
    except KeyboardInterrupt:
        # exit more gracefully without a traceback
        print(INTERRUPT_MSG)
        exit(0)
    selected_app_action = AppAction(selected_app_action)
    return selected_app_action


def prompt_user_for_work_action():
    selected_work_action = questionary.select(
        "What do you want to do with this work?",
        choices=[act.value for act in WorkAction],
    ).unsafe_ask()
    selected_work_action = WorkAction(selected_work_action)
    return selected_work_action


def does_work_need_updating(work: AO3.Work, work_dir: Path) -> bool:
    """Checks whether an AO3 work needs updating

    Args:
        work (AO3.Work): _description_
        work_dir (Path): _description_

    Returns:
        bool: _description_
    """
    # read in the metadata file
    try:
        work_metadata = MetadataFile.read_from_work_dir(work_dir)
    except MetadataFileParseError:
        print("Invalid metadata file, overwriting...")
    except FileNotFoundError:
        print(f"Adding new work {work.title}")
    else:
        # check whether the AO3 updated date is more recent than
        # the updated data for the saved file
        if not work_metadata.needs_updated(work):
            print(f"{work.title} is already up to date, skipping")
            return False
        else:
            new_chapters = work.nchapters - work_metadata.chapters_published
            print(
                f"Updating {work.title} ({new_chapters} new chapter{'s' if new_chapters != 1 else ''})"
            )
    return True


def mark_work_read(work_path: Path):
    """Ask a user how much they've read, save that to the work's metadata

    Args:
        work_path (Path): Path to work
    """
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


def list_downloaded_works(all_works: list[Path]):
    """Print a list of downloaded works

    Args:
        all_works (list[Path]): List of paths to works
    """
    print("\n  Downloaded Works:")
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


def work_folder_to_name(input_string: str) -> str:
    last_space_index = input_string.rfind(" ")
    return input_string[:last_space_index]


def work_folder_to_id(input_string: str) -> str:
    last_space_index = input_string.rfind(" ")
    return input_string[last_space_index + 1 :]


def sanitize_path(input_string: str) -> str:
    return re.sub(r'[\\/:"*?<>|]', "", input_string)
