import csv
import io
from enum import IntEnum
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from playlistparser.exceptions import (
    MalformedPlaylistError,
    MissingFieldError,
    PlaylistParserError,
    UnknownFormatError,
)
from playlistparser.parsers.engine import iter_tracks as engine_iter
from playlistparser.parsers.rekordbox import iter_tracks as rekordbox_iter
from playlistparser.parsers.serato import iter_tracks as serato_iter
from playlistparser.parsers.traktor import iter_tracks as traktor_iter
from playlistparser.parsers.traktor import track_total as traktor_track_total
from playlistparser.parsers.virtualdj import iter_tracks as virtualdj_iter
from playlistparser.progress import CountingReader, ProgressCallback
from playlistparser.track import Track
from playlistparser.utils import decoded_text

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Iterable, Iterator
    from typing import BinaryIO

type ParserFunction = Callable[..., Iterator[Track]]

FieldName = Literal[
    "title",
    "artist",
    "album",
    "key",
    "duration",
    "year",
    "bpm",
    "file_path",
    "vendor_id",
]


class PlaylistType(IntEnum):
    UNKNOWN = 0
    ENGINE = 1
    REKORDBOX = 2
    SERATO = 3
    TRAKTOR = 4
    VIRTUALDJ = 5


DELIMITED_FORMATS: dict[PlaylistType, tuple[str, str, int, str | None]] = {
    PlaylistType.ENGINE: ("utf-8", ",", 1, None),
    PlaylistType.REKORDBOX: ("utf-16", "\t", 1, "replace"),
    PlaylistType.SERATO: ("utf-8", ",", 2, None),
    PlaylistType.VIRTUALDJ: ("utf-8-sig", ",", 2, None),
}

PARSERS: dict[PlaylistType, ParserFunction] = {
    PlaylistType.ENGINE: engine_iter,
    PlaylistType.REKORDBOX: rekordbox_iter,
    PlaylistType.SERATO: serato_iter,
    PlaylistType.TRAKTOR: traktor_iter,
    PlaylistType.VIRTUALDJ: virtualdj_iter,
}

SUPPORTED_FIELDS_BY_TYPE: dict[PlaylistType, frozenset[FieldName]] = {
    PlaylistType.ENGINE: frozenset({"title", "artist", "album", "duration", "year", "bpm", "file_path"}),
    PlaylistType.REKORDBOX: frozenset({"title", "artist", "album", "key", "duration", "year", "bpm", "file_path"}),
    PlaylistType.SERATO: frozenset({"title", "artist", "year"}),
    PlaylistType.TRAKTOR: frozenset(
        {"title", "artist", "album", "key", "duration", "year", "bpm", "file_path", "vendor_id"}
    ),
    PlaylistType.VIRTUALDJ: frozenset({"title", "artist", "key", "duration", "year", "bpm"}),
}


def sniff_csv_stream(file: BinaryIO, path: Path) -> PlaylistType:
    """Read a CSV header from *file* and restore its original position."""
    position = file.tell()
    try:
        first_line = file.readline()
        header = next(csv.reader([first_line.decode("utf-8")]))
    except StopIteration, UnicodeDecodeError, csv.Error:
        raise UnknownFormatError(path) from None
    finally:
        file.seek(position)

    if header and "\ufeff" in header[0]:
        return PlaylistType.VIRTUALDJ
    if "#" in header:
        return PlaylistType.ENGINE
    if "name" in header:
        return PlaylistType.SERATO
    raise UnknownFormatError(path)


def sniff_csv(path: Path) -> PlaylistType:
    """Read the first header row of a CSV file and return its format."""
    with path.open("rb") as file:
        return sniff_csv_stream(file, path)


def resolve_format(path: Path) -> PlaylistType:
    """Return the :class:`PlaylistType` for *path* (does I/O for CSV)."""
    name = path.name
    if name.endswith(".nml"):
        return PlaylistType.TRAKTOR
    if name.endswith(".txt"):
        return PlaylistType.REKORDBOX
    if name.endswith(".csv"):
        return sniff_csv(path)
    raise UnknownFormatError(path)


def count_delimited_tracks(file: io.FileIO, playlist_type: PlaylistType) -> int:
    """Count logical data records, including CSV records containing newlines."""
    encoding, delimiter, metadata_rows, errors = DELIMITED_FORMATS[playlist_type]
    buffered = io.BufferedReader(file)
    try:
        with decoded_text(buffered, encoding=encoding, errors=errors) as text:
            reader = csv.reader(text, delimiter=delimiter)
            record_count = 0
            for record in reader:
                del record
                record_count += 1
    finally:
        buffered.detach()
    return max(0, record_count - metadata_rows)


def source_track_total(file: io.FileIO, playlist_type: PlaylistType) -> int | None:
    """Return an exact source-record count when the format exposes one cheaply."""
    if playlist_type == PlaylistType.TRAKTOR:
        return traktor_track_total(file)
    if playlist_type in DELIMITED_FORMATS:
        return count_delimited_tracks(file, playlist_type)
    return None


class PlaylistParser:
    """Parse a DJ playlist file.

    Accepts a ``str`` or :class:`os.PathLike` path.  Format detection is
    lazy for CSV files (no I/O in the constructor).

    Example::

        pl = PlaylistParser("set.nml")
        for track in pl:  # streaming — no materialisation
            print(track)

        tracks = PlaylistParser("set.nml").to_list()  # explicit materialisation

        pl = PlaylistParser("history.csv")
        print(pl.playlist_type)  # PlaylistType.SERATO / ENGINE / VIRTUALDJ
        print(pl.track_count)  # materialises once, cached thereafter
        print(pl.total_duration)  # seconds
    """

    def __init__(
        self,
        file_path: str | os.PathLike[str],
        *,
        require: Iterable[FieldName] = (),
        as_type: PlaylistType | None = None,
        default_artist: str = "Unknown Artist",
    ) -> None:
        self.path = Path(file_path)
        self.default_artist = default_artist
        self.require: frozenset[FieldName] = frozenset(require)
        self.resolved_type: PlaylistType | None = as_type
        self.cached_tracks: list[Track] | None = None

        # Extension-only detection — no I/O.  CSV sniffing is deferred.
        if as_type is None:
            name = self.path.name
            if name.endswith(".nml"):
                self.resolved_type = PlaylistType.TRAKTOR
            elif name.endswith(".txt"):
                self.resolved_type = PlaylistType.REKORDBOX
            elif not name.endswith(".csv"):
                raise UnknownFormatError(self.path)
            # .csv → resolved_type stays None until first access

    @property
    def playlist_type(self) -> PlaylistType:
        """Format of the playlist, detected lazily for CSV files."""
        if self.resolved_type is None:
            self.resolved_type = sniff_csv(self.path)
        return self.resolved_type

    @property
    def track_count(self) -> int:
        """Total number of tracks (materialises if not yet accessed)."""
        return len(self.materialise())

    @property
    def total_duration(self) -> int:
        """Sum of all track durations in seconds (materialises if not yet accessed)."""
        return sum(track.duration for track in self.materialise())

    def __iter__(self) -> Iterator[Track]:
        """Yield tracks one by one; always a fresh streaming pass."""
        yield from self.stream()

    def to_list(self) -> list[Track]:
        """Materialise all tracks into a list.

        The result is cached; subsequent calls return the same list without
        re-reading the file.
        """
        return self.materialise()

    def materialise(self) -> list[Track]:
        """Return the cached track list, populating it on first call."""
        if self.cached_tracks is None:
            self.cached_tracks = list(self.stream())
        return self.cached_tracks

    def validate_required_fields(self, playlist_type: PlaylistType) -> None:
        """Reject fields that the detected format cannot provide."""
        unsupported = self.require - SUPPORTED_FIELDS_BY_TYPE.get(playlist_type, frozenset())
        if unsupported:
            raise MissingFieldError(min(unsupported))

    def located(self, tracks: Iterator[Track]) -> Iterator[Track]:
        """Re-raise parser structural errors with the playlist path attached."""
        try:
            yield from tracks
        except MalformedPlaylistError as error:
            raise MalformedPlaylistError(str(error), path=self.path, line=error.line) from error
        except UnicodeDecodeError as error:
            # Bytes that do not decode as the detected format's encoding mean the extension
            # lied about the format, so report a detection failure instead of leaking a codec
            # error to the caller.
            raise UnknownFormatError(self.path) from error

    def stream(self, *, on_progress: ProgressCallback | None = None) -> Iterator[Track]:
        """Yield tracks and optionally report source and output progress."""
        detected_type = self.resolved_type
        parser_function = PARSERS.get(detected_type) if detected_type is not None else None
        if detected_type is not None:
            self.validate_required_fields(detected_type)
            if parser_function is None:
                raise UnknownFormatError(self.path)

        with self.path.open("rb", buffering=0) as source:
            if detected_type is None:
                detected_type = sniff_csv_stream(source, self.path)
                self.resolved_type = detected_type
                self.validate_required_fields(detected_type)
                parser_function = PARSERS.get(detected_type)

            if parser_function is None:
                raise UnknownFormatError(self.path)

            if on_progress is None:
                source.seek(0)
                with io.BufferedReader(source) as buffered:
                    yield from self.located(
                        parser_function(
                            buffered,
                            require=self.require,
                            default_artist=self.default_artist,
                        ),
                    )
                return

            bytes_total = source.seek(0, io.SEEK_END)
            source.seek(0)
            try:
                total_tracks = source_track_total(source, detected_type)
            except UnicodeDecodeError as error:
                raise UnknownFormatError(self.path) from error
            source.seek(0)

            tracks_done = 0
            last_progress: tuple[int, int | None, int, int] | None = None
            progress_callback = on_progress

            def emit_progress(bytes_read: int) -> None:
                nonlocal last_progress
                progress = (tracks_done, total_tracks, min(bytes_read, bytes_total), bytes_total)
                if progress == last_progress:
                    return
                last_progress = progress
                progress_callback(*progress)

            emit_progress(0)
            counting_reader = CountingReader(source, emit_progress)
            with io.BufferedReader(counting_reader) as buffered:
                for track in self.located(
                    parser_function(
                        buffered,
                        require=self.require,
                        default_artist=self.default_artist,
                    ),
                ):
                    tracks_done += 1
                    emit_progress(counting_reader.bytes_read)
                    yield track
                emit_progress(bytes_total)


__all__ = [
    "FieldName",
    "MalformedPlaylistError",
    "MissingFieldError",
    "PlaylistParser",
    "PlaylistParserError",
    "PlaylistType",
    "ProgressCallback",
    "Track",
    "UnknownFormatError",
]

__version__ = "4.4.1"
