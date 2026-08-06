import csv
import logging
from functools import partial
from typing import TYPE_CHECKING

from playlistparser.track import Track
from playlistparser.utils import csv_field, decoded_text, required, time_str_to_seconds

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

    from playlistparser import FieldName

logger = logging.getLogger(__name__)

TITLE_COL = "Track Title"
ARTIST_COL = "Artist"
ALBUM_COL = "Album"
KEY_COL = "Key"
TIME_COL = "Time"
BPM_COL = "BPM"
YEAR_COL = "Year"
FILE_COL = "Location"


def iter_tracks(
    file: BinaryIO,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """Rekordbox supports: title, artist, album, key, year, duration, bpm, file_path.

    The export file is UTF-16 tab-separated.  We wrap the binary stream in
    :class:`io.TextIOWrapper` so the CSV reader processes it line-by-line
    without loading the entire file into RAM.

    Yields one :class:`~playlistparser.track.Track` per playlist row.
    """
    with decoded_text(file, encoding="utf-16", errors="replace") as text:
        reader = csv.reader(text, delimiter="\t")

        try:
            raw_header = next(reader)
        except StopIteration:
            return

        headers = [header.strip() for header in raw_header]
        columns: dict[str, int] = {name: position for position, name in enumerate(headers)}

        for lineno, row in enumerate(reader, start=2):
            title = required(csv_field(row, columns, TITLE_COL), "title", require, line=lineno) or "Unknown"
            field = partial(required, require=require, line=lineno, track_title=title)

            raw_time = field(csv_field(row, columns, TIME_COL), "duration")
            playtime = time_str_to_seconds(raw_time) if raw_time else 0

            raw_bpm = field(csv_field(row, columns, BPM_COL), "bpm")
            try:
                bpm = float(raw_bpm) if raw_bpm else 0.0
            except ValueError:
                bpm = 0.0

            year = field(csv_field(row, columns, YEAR_COL), "year")
            track_path = field(csv_field(row, columns, FILE_COL), "file_path")
            artist = field(csv_field(row, columns, ARTIST_COL), "artist") or default_artist
            album = field(csv_field(row, columns, ALBUM_COL), "album")
            key = field(csv_field(row, columns, KEY_COL), "key")

            yield Track(
                title=title,
                artist=artist,
                album=album,
                key=key,
                year=year,
                duration=playtime,
                bpm=bpm,
                file_path=track_path,
            )
