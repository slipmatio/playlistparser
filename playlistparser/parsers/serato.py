import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track
from playlistparser.utils import csv_field

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playlistparser import FieldName

logger = logging.getLogger(__name__)

NAME_COL = "name"
ARTIST_COL = "artist"
YEAR_COL = "year"

# Serato exports a session-timestamp pseudo-row immediately after the header.
SESSION_TIMESTAMP_LINENO = 2


def iter_tracks(
    file_path: str,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """Serato supports: title, artist, year.

    The first data row is a session date header — skip it (lineno == 2).

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    with Path(file_path).open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            return

        headers = [header.strip() for header in raw_header]
        columns: dict[str, int] = {name: position for position, name in enumerate(headers)}

        for lineno, row in enumerate(reader, start=2):
            # First data row is the session timestamp line — skip it.
            if lineno == SESSION_TIMESTAMP_LINENO:
                continue

            try:
                title = csv_field(row, columns, NAME_COL)
                if not title and "title" in require:
                    raise MissingFieldError("title", line=lineno)

                artist = csv_field(row, columns, ARTIST_COL)
                if not artist and "artist" in require:
                    raise MissingFieldError("artist", line=lineno, track_title=title or None)
                artist = artist or default_artist

                year = csv_field(row, columns, YEAR_COL)
                if not year and "year" in require:
                    raise MissingFieldError("year", line=lineno, track_title=title or None)

                yield Track(title=title, artist=artist, year=year)
            except MissingFieldError:
                raise
            except (csv.Error, IndexError, ValueError, TypeError) as exc:
                logger.debug("Skipping line %d: %s", lineno, exc)
