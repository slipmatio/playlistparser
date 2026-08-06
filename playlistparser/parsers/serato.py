import csv
import logging
from functools import partial
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track
from playlistparser.utils import csv_field, decoded_text, required

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

    from playlistparser import FieldName

logger = logging.getLogger(__name__)

NAME_COL = "name"
ARTIST_COL = "artist"
YEAR_COL = "year"

# Serato exports a session-timestamp pseudo-row immediately after the header.
SESSION_TIMESTAMP_LINENO = 2


def iter_tracks(
    file: BinaryIO,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """Serato supports: title, artist, year.

    The first data row is a session date header — skip it (lineno == 2).

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    with decoded_text(file, encoding="utf-8") as text:
        reader = csv.reader(text)
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
                title = required(csv_field(row, columns, NAME_COL), "title", require, line=lineno)
                field = partial(required, require=require, line=lineno, track_title=title)

                artist = field(csv_field(row, columns, ARTIST_COL), "artist") or default_artist
                year = field(csv_field(row, columns, YEAR_COL), "year")

                yield Track(title=title, artist=artist, year=year)
            except MissingFieldError:
                raise
            except (csv.Error, IndexError, ValueError, TypeError) as exc:
                logger.debug("Skipping line %d: %s", lineno, exc)
