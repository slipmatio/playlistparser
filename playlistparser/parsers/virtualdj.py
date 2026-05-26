import csv
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

TITLE_COL = "Title"
ARTIST_COL = "Artist"
LENGTH_COL = "Length"
BPM_COL = "Bpm"
YEAR_COL = "Year"


def iter_tracks(
    file_path: str,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """VirtualDJ supports: title, artist, year, duration, bpm.

    The first row is the BOM+``sep=,`` directive; the second row is the real
    header.  We skip row 1 and build the index map from row 2.

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    # utf-8-sig strips the BOM so row 0 reads as plain 'sep=,'
    with Path(file_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            next(reader)  # skip 'sep=,' directive row
            raw_header = next(reader)
        except StopIteration:
            return

        headers = [header.strip() for header in raw_header]
        columns: dict[str, int] = {name: position for position, name in enumerate(headers)}

        for lineno, row in enumerate(reader, start=3):
            try:
                title = csv_field(row, columns, TITLE_COL)
                if not title and "title" in require:
                    raise MissingFieldError("title", line=lineno)

                artist = csv_field(row, columns, ARTIST_COL) or default_artist

                raw_length = csv_field(row, columns, LENGTH_COL)
                try:
                    playtime = time_str_to_seconds(raw_length) if raw_length else 0
                except ValueError, AttributeError:
                    playtime = 0
                if playtime == 0 and "duration" in require:
                    raise MissingFieldError("duration", line=lineno, track_title=title or None)

                raw_bpm = csv_field(row, columns, BPM_COL)
                try:
                    bpm = int(float(raw_bpm)) if raw_bpm else 0
                except ValueError, AttributeError:
                    bpm = 0
                if bpm == 0 and "bpm" in require:
                    raise MissingFieldError("bpm", line=lineno, track_title=title or None)

                year = csv_field(row, columns, YEAR_COL)
                if not year and "year" in require:
                    raise MissingFieldError("year", line=lineno, track_title=title or None)

                yield Track(title=title, artist=artist, year=year, duration=playtime, bpm=bpm)
            except MissingFieldError:
                raise
            except (csv.Error, IndexError, ValueError, TypeError) as exc:
                logger.debug("Skipping line %d: %s", lineno, exc)
