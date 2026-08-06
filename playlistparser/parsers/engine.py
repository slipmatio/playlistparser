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

TITLE_COL = "Title"
ARTIST_COL = "Artist"
ALBUM_COL = "Album"
YEAR_COL = "Year"
BPM_COL = "BPM"
LENGTH_COL = "Length"
FILE_COL = "File name"
HISTORY_PATH_MARKER = "#history#"


def resolve_history_metadata(
    *,
    title: str,
    artist: str,
    track_path: str,
) -> tuple[str, str]:
    """Recover metadata embedded in titles by Engine DJ history exports.

    Returns an empty artist when none could be recovered, so the caller can
    tell a genuinely missing artist from a defaulted one.
    """
    if artist:
        return artist, title

    if HISTORY_PATH_MARKER in track_path:
        history_artist, separator, history_title = title.partition(" - ")
        if separator and history_artist.strip() and history_title.strip():
            return history_artist.strip(), history_title.strip()

    return "", title


def iter_tracks(
    file: BinaryIO,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """Engine DJ supports: title, artist, album, year, duration, bpm, file_path.

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
            try:
                title = required(csv_field(row, columns, TITLE_COL), "title", require, line=lineno) or "Unknown"

                track_path = csv_field(row, columns, FILE_COL)
                artist, title = resolve_history_metadata(
                    title=title,
                    artist=csv_field(row, columns, ARTIST_COL),
                    track_path=track_path,
                )
                field = partial(required, require=require, line=lineno, track_title=title)

                artist = field(artist, "artist") or default_artist
                album = field(csv_field(row, columns, ALBUM_COL), "album")
                year = field(csv_field(row, columns, YEAR_COL), "year")
                field(track_path, "file_path")

                raw_bpm = field(csv_field(row, columns, BPM_COL), "bpm")
                try:
                    bpm = float(raw_bpm) if raw_bpm else 0.0
                except ValueError:
                    bpm = 0.0

                raw_duration = field(csv_field(row, columns, LENGTH_COL), "duration")
                try:
                    playtime = int(raw_duration) if raw_duration else 0
                except ValueError:
                    playtime = 0

                yield Track(
                    title=title,
                    artist=artist,
                    album=album,
                    year=year,
                    duration=playtime,
                    bpm=bpm,
                    file_path=track_path,
                )
            except MissingFieldError:
                raise
            except (csv.Error, IndexError, ValueError, TypeError) as exc:
                logger.debug("Skipping line %d: %s", lineno, exc)
