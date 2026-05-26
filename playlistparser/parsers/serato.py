import csv
import logging
from collections.abc import Iterator
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track

if TYPE_CHECKING:
    from playlistparser import FieldName

logger = logging.getLogger(__name__)

NAME_COL = "name"
ARTIST_COL = "artist"
YEAR_COL = "year"


def get_field(row: list[str], idx: dict[str, int], col: str, default: str = "") -> str:
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
    """
    Serato supports: title, artist, year.

    The first data row is a session date header — skip it (lineno == 2).

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    log = logger or logging.getLogger(__name__)
    with open(file_path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            return

        header = [h.strip() for h in raw_header]
        idx: dict[str, int] = {col: i for i, col in enumerate(header)}

        for lineno, row in enumerate(reader, start=2):
            # First data row is the session timestamp line — skip it.
            if lineno == 2:
                continue

            try:
                title = get_field(row, idx, NAME_COL)
                if not title and "title" in require:
                    raise MissingFieldError("title", line=lineno)

                artist = get_field(row, idx, ARTIST_COL)
                if not artist and "artist" in require:
                    raise MissingFieldError("artist", line=lineno, track_title=title or None)
                artist = artist or default_artist

                year = get_field(row, idx, YEAR_COL)
                if not year and "year" in require:
                    raise MissingFieldError("year", line=lineno, track_title=title or None)

                yield Track(title=title, artist=artist, year=year)
            except MissingFieldError:
                raise
            except Exception as exc:
                log.debug("Skipping line %d: %s", lineno, exc)
