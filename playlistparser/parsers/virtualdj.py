import csv
import logging
from functools import partial
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track
from playlistparser.utils import csv_field, decoded_text, required, time_str_to_seconds

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

    from playlistparser import FieldName

logger = logging.getLogger(__name__)

TITLE_COL = "Title"
ARTIST_COL = "Artist"
LENGTH_COL = "Length"
BPM_COL = "Bpm"
KEY_COL = "Key"
YEAR_COL = "Year"


def iter_tracks(
    file: BinaryIO,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """VirtualDJ supports: title, artist, key, year, duration, bpm.

    The first row is the BOM+``sep=,`` directive; the second row is the real
    header.  We skip row 1 and build the index map from row 2.

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    # utf-8-sig strips the BOM so row 0 reads as plain 'sep=,'
    with decoded_text(file, encoding="utf-8-sig") as text:
        reader = csv.reader(text)
        try:
            next(reader)  # skip 'sep=,' directive row
            raw_header = next(reader)
        except StopIteration:
            return

        headers = [header.strip() for header in raw_header]
        columns: dict[str, int] = {name: position for position, name in enumerate(headers)}

        for lineno, row in enumerate(reader, start=3):
            try:
                title = required(csv_field(row, columns, TITLE_COL), "title", require, line=lineno)
                field = partial(required, require=require, line=lineno, track_title=title)

                artist = field(csv_field(row, columns, ARTIST_COL), "artist") or default_artist
                key = field(csv_field(row, columns, KEY_COL), "key")
                year = field(csv_field(row, columns, YEAR_COL), "year")

                raw_length = csv_field(row, columns, LENGTH_COL)
                try:
                    playtime = time_str_to_seconds(raw_length) if raw_length else 0
                except ValueError, AttributeError:
                    playtime = 0
                field(playtime, "duration")

                raw_bpm = csv_field(row, columns, BPM_COL)
                try:
                    bpm = float(raw_bpm) if raw_bpm else 0.0
                except ValueError, AttributeError:
                    bpm = 0.0
                field(bpm, "bpm")

                yield Track(title=title, artist=artist, key=key, year=year, duration=playtime, bpm=bpm)
            except MissingFieldError:
                raise
            except (csv.Error, IndexError, ValueError, TypeError) as exc:
                logger.debug("Skipping line %d: %s", lineno, exc)
