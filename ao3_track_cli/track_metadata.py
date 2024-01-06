from __future__ import annotations  # for classmethod annotations
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import os

import AO3

from constants import DATETIME_FORMAT

METADATA_FILENAME = ".ao3_track_cli_metadata.json"
STALE_WORK_THRESHOLD = timedelta(days=365)


class MetadataFileParseError(Exception):
    """Some problem reading/parsing the metadata json file"""

    ...


@dataclass
class MetadataFile:
    """For storing metadata about a downloaded AO3 work

    Includes helpers for writing/reading to a json file"""

    date_updated: str
    work_id: int
    chapters_published: int
    chapters_expected: int | None
    chapters_read: int = 0

    @property
    def chapter_count_str(self) -> str:
        """Formatted string of (read/published/total) chapters

        Returns:
            str
        """
        return f"{self.chapters_read}/{self.chapters_published}/{self.chapters_expected or '?'}"

    @property
    def is_stale(self) -> bool:
        if self.chapters_published == self.chapters_expected:
            return False
        last_edit = datetime.strptime(self.date_updated, DATETIME_FORMAT)
        return (datetime.now() - last_edit) > STALE_WORK_THRESHOLD

    @classmethod
    def read_from_work_dir(cls, work_dir: Path) -> MetadataFile:
        """Ingest metadata json file into this object

        Args:
            work_dir (Path): Path to work dir that contains metadata json

        Raises:
            MetadataFileParseError: Error parsing file

        Returns:
            MetadataFile
        """
        with open(work_dir / METADATA_FILENAME, "r", encoding="utf-8") as updatefile:
            file_contents = json.load(updatefile)
            try:
                update_info = MetadataFile(**file_contents)
            except TypeError:
                # probably importing an older version of this file with missing pieces
                # will have to take it from scratch
                print(
                    f"Disreguarding invalid/oudated contents of {work_dir / METADATA_FILENAME}"
                )
                raise MetadataFileParseError
        return update_info

    def write_to_work_dir(self, work_dir: Path):
        """Write to a metadata json file inside work_dir

        Args:
            work_dir (Path)
        """
        file_path = work_dir / METADATA_FILENAME
        # I want the filename to start with a period but you get a PermissionError
        # on Windows - so instead we write to a regular file and then rename it
        # this is really dumb but I couldn't find any other way so
        temp_path = "ydj2904ytc0294y2c9y09x2s49.file"  # so it doesn't overwrite anything (hopefully)
        with open(temp_path, "w", encoding="utf-8") as updatefile:
            json.dump(asdict(self), updatefile)
        # delete the existing file
        if file_path.exists():
            os.remove(file_path)
        # replace it with this one
        os.rename(temp_path, file_path)

    def needs_updated(self, work: AO3.Work) -> bool:
        """Whether a given work needs updating

        Args:
            work (AO3.Work)

        Returns:
            bool: Whether there's anything to update
        """
        try:
            last_update = datetime.strptime(self.date_updated, DATETIME_FORMAT)
        except ValueError:
            print("Error parsing metadata contents, treating this work as brand new")
            return True
        return work.date_updated > last_update
