"""Tools for dealing with AO3 api related objects"""

from pathlib import Path
import AO3
import questionary


def users_to_str(users: list[AO3.User]) -> str:
    """Take a list of AO3 users and convert it to a string.

    Args:
        users (list[AO3.User]): List of users, probably from AO3.Work.authors

    Returns:
        str: e.g. "Author1, Author2"
    """
    return ", ".join([u.username for u in users])


def write_human_readable_work_info(work: AO3.Work, info_file_path: Path):
    """Write a bunch of human readable info about a work to a file

    Args:
        work (AO3.Work): _description_
        info_file_path (Path): _description_
    """
    with open(info_file_path, "w", encoding="utf-8") as infofile:
        infofile.write(f"Title: {work.title}\n")
        infofile.write(f"Author(s): {users_to_str(work.authors)}\n")
        infofile.write(f"URL: {work.url}\n")
        infofile.write(f"Series: {work.series}\n")
        infofile.write("\n")
        infofile.write(f"Words: {work.words}\n")
        infofile.write(f"Chapters: {work.nchapters}/{work.expected_chapters or '?'}\n")
        infofile.write(f"Kudos: {work.kudos}\n")
        infofile.write(f"Hits: {work.hits}\n")
        infofile.write("\n")
        # published should always be first
        infofile.write(f"Date Published: {work.date_published}\n")
        # edited is down to the minute, updated is I THINK the same day
        # but doesn't have the time
        infofile.write(f"Date Edited: {work.date_edited}\n")
        infofile.write(f"Date Updated: {work.date_updated}\n")
        infofile.write("\n")
        infofile.write(f"Rating: {work.rating}\n")
        infofile.write(f"Warnings: {work.warnings}\n")
        infofile.write(f"Categories: {work.categories}\n")
        infofile.write("\n")
        infofile.write(f"Characters: {work.characters}\n")
        infofile.write(f"Relationships: {work.relationships}\n")
        infofile.write(f"Fandoms: {work.fandoms}\n")
        infofile.write(f"Tags: {work.tags}\n")
        infofile.write("\n")
        infofile.write(f"Summary: {work.summary}\n")
        infofile.write("\n")
        infofile.write(f"Start Notes: {work.start_notes}\n")


def chapter_text_for_humans(chapter: AO3.Chapter) -> str:
    """Turn an AO# chapter into human-readable plaintext to be written to file

    Args:
        chapter (AO3.Chapter)

    Returns:
        str
    """
    out_str = ""
    out_str += f"{chapter.work.title} - Chapter {chapter.number}"
    if chapter.title:
        out_str += f"- {chapter.title}"
    out_str += " \n"
    out_str += f"URL: {chapter.url} \n"
    out_str += f"Words: {chapter.words} \n"
    if chapter.summary:
        out_str += f"Summary: {chapter.summary}"
    if chapter.start_notes:
        out_str += f"Start Notes: {chapter.start_notes}"
    out_str += " \n"
    # time for the meat and potatoes
    out_str += chapter.text
    out_str += " \n"
    if chapter.end_notes:
        out_str += f"End Notes: {chapter.end_notes}"
    return out_str


def get_work_id_from_user() -> str:
    """Solicit user input to get a work's ID

    Raises:
        ValueError: Invalid user input

    Returns:
        str: AO3 Work ID
    """
    new_work_from_user = questionary.text(
        "Please enter the work's URL or ID.",
        validate=lambda x: bool(x),
    ).unsafe_ask()
    if new_work_from_user.isdigit():
        # user directly provided work ID
        work_id = new_work_from_user
    elif "archiveofourown.org" in new_work_from_user:
        # user provided a url
        work_id = AO3.utils.workid_from_url(new_work_from_user)
    else:
        raise ValueError("Must provide an AO3 URL or ID")
    return str(work_id)
