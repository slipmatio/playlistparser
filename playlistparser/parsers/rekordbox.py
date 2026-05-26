import csv
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track
from playlistparser.utils import time_str_to_seconds

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


def _get_field(row: list[str], idx: dict[str, int], col: str, default: str = "") -> str:
    i = idx.get(col)
    if i is None or i >= len(row):
        return default
    return row[i].strip()


def iter_tracks(
    file_path: str,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
    logger: logging.Logger | None = None,
) -> Iterator[Track]:
    """Rekordbox supports: title, artist, year, duration, bpm, file_path.

    The export file is UTF-16 tab-separated.  We wrap the binary stream in
    :class:`io.TextIOWrapper` so the CSV reader processes it line-by-line
    without loading the entire file into RAM.

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    del logger  # Rekordbox currently raises malformed row errors directly.
    with Path(file_path).open("rb") as raw:
        text = io.TextIOWrapper(raw, encoding="utf-16", errors="replace", newline="")
        reader = csv.reader(text, delimiter="\t")

        try:
            raw_header = next(reader)
        except StopIteration:
            return

        header = [h.strip() for h in raw_header]
        idx: dict[str, int] = {col: i for i, col in enumerate(header)}

        for lineno, row in enumerate(reader, start=2):
            title = _get_field(row, idx, TITLE_COL)
            if not title:
                if "title" in require:
                    raise MissingFieldError("title", line=lineno)
                title = "Unknown"

            raw_time = _get_field(row, idx, TIME_COL)
            if not raw_time:
                if "duration" in require:
                    raise MissingFieldError("duration", line=lineno, track_title=title)
                playtime = 0
            else:
                playtime = time_str_to_seconds(raw_time)

            raw_bpm = _get_field(row, idx, BPM_COL)
            if not raw_bpm:
                if "bpm" in require:
                    raise MissingFieldError("bpm", line=lineno, track_title=title)
                bpm = 0
            else:
                try:
                    bpm = int(float(raw_bpm))
                except ValueError:
                    bpm = 0

            year = _get_field(row, idx, YEAR_COL)
            if not year and "year" in require:
                raise MissingFieldError("year", line=lineno, track_title=title)

            fp = _get_field(row, idx, FILE_COL)
            if not fp and "file_path" in require:
                raise MissingFieldError("file_path", line=lineno, track_title=title)

            artist = _get_field(row, idx, ARTIST_COL) or default_artist

            yield Track(
                title=title,
                artist=artist,
                year=year,
                duration=playtime,
                bpm=bpm,
                file_path=fp,
            )
