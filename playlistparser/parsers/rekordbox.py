import csv
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track
from playlistparser.utils import csv_field, time_str_to_seconds

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playlistparser import FieldName

logger = logging.getLogger(__name__)

TITLE_COL = "Track Title"
ARTIST_COL = "Artist"
TIME_COL = "Time"
BPM_COL = "BPM"
YEAR_COL = "Year"
FILE_COL = "Location"


def iter_tracks(
    file_path: str,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """Rekordbox supports: title, artist, year, duration, bpm, file_path.

    The export file is UTF-16 tab-separated.  We wrap the binary stream in
    :class:`io.TextIOWrapper` so the CSV reader processes it line-by-line
    without loading the entire file into RAM.

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    with Path(file_path).open("rb") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-16", errors="replace", newline="")
        reader = csv.reader(text, delimiter="\t")

        try:
            raw_header = next(reader)
        except StopIteration:
            return

        headers = [header.strip() for header in raw_header]
        columns: dict[str, int] = {name: position for position, name in enumerate(headers)}

        for lineno, row in enumerate(reader, start=2):
            title = csv_field(row, columns, TITLE_COL)
            if not title:
                if "title" in require:
                    raise MissingFieldError("title", line=lineno)
                title = "Unknown"

            raw_time = csv_field(row, columns, TIME_COL)
            if not raw_time:
                if "duration" in require:
                    raise MissingFieldError("duration", line=lineno, track_title=title)
                playtime = 0
            else:
                playtime = time_str_to_seconds(raw_time)

            raw_bpm = csv_field(row, columns, BPM_COL)
            if not raw_bpm:
                if "bpm" in require:
                    raise MissingFieldError("bpm", line=lineno, track_title=title)
                bpm = 0
            else:
                try:
                    bpm = int(float(raw_bpm))
                except ValueError:
                    bpm = 0

            year = csv_field(row, columns, YEAR_COL)
            if not year and "year" in require:
                raise MissingFieldError("year", line=lineno, track_title=title)

            track_path = csv_field(row, columns, FILE_COL)
            if not track_path and "file_path" in require:
                raise MissingFieldError("file_path", line=lineno, track_title=title)

            artist = csv_field(row, columns, ARTIST_COL) or default_artist

            yield Track(
                title=title,
                artist=artist,
                year=year,
                duration=playtime,
                bpm=bpm,
                file_path=track_path,
            )
