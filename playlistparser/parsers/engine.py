import csv
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from playlistparser.exceptions import MissingFieldError
from playlistparser.track import Track

if TYPE_CHECKING:
    from collections.abc import Iterator

    from playlistparser import FieldName

logger = logging.getLogger(__name__)

TITLE_COL = "Title"
ARTIST_COL = "Artist"
YEAR_COL = "Year"
BPM_COL = "BPM"
LENGTH_COL = "Length"
FILE_COL = "File name"


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
) -> Iterator[Track]:
    """Engine DJ supports: title, artist, year, duration, bpm, file_path.

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    with Path(file_path).open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            raw_header = next(reader)
        except StopIteration:
            return

        header = [h.strip() for h in raw_header]
        idx: dict[str, int] = {col: i for i, col in enumerate(header)}

        for lineno, row in enumerate(reader, start=2):
            try:
                title = _get_field(row, idx, TITLE_COL)
                if not title:
                    if "title" in require:
                        raise MissingFieldError("title", line=lineno)
                    title = "Unknown"

                artist = _get_field(row, idx, ARTIST_COL) or default_artist

                year = _get_field(row, idx, YEAR_COL)
                if not year and "year" in require:
                    raise MissingFieldError("year", line=lineno, track_title=title)

                raw_bpm = _get_field(row, idx, BPM_COL)
                if not raw_bpm and "bpm" in require:
                    raise MissingFieldError("bpm", line=lineno, track_title=title)
                try:
                    bpm = int(raw_bpm) if raw_bpm else 0
                except ValueError:
                    bpm = 0

                raw_duration = _get_field(row, idx, LENGTH_COL)
                if not raw_duration and "duration" in require:
                    raise MissingFieldError("duration", line=lineno, track_title=title)
                try:
                    playtime = int(raw_duration) if raw_duration else 0
                except ValueError:
                    playtime = 0

                fp = _get_field(row, idx, FILE_COL)
                if not fp and "file_path" in require:
                    raise MissingFieldError("file_path", line=lineno, track_title=title)

                yield Track(
                    title=title,
                    artist=artist,
                    year=year,
                    duration=playtime,
                    bpm=bpm,
                    file_path=fp,
                )
            except MissingFieldError:
                raise
            except (csv.Error, IndexError, ValueError, TypeError) as exc:
                logger.debug("Skipping line %d: %s", lineno, exc)
