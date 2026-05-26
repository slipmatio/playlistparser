"""playlistparser — public API."""

import csv
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
from playlistparser.parsers.virtualdj import iter_tracks as virtualdj_iter
from playlistparser.track import Track

if TYPE_CHECKING:
    import os
    from collections.abc import Iterable, Iterator

FieldName = Literal["title", "artist", "duration", "year", "bpm", "file_path"]


class PlaylistType(IntEnum):
    UNKNOWN = 0
    ENGINE = 1
    REKORDBOX = 2
    SERATO = 3
    TRAKTOR = 4
    VIRTUALDJ = 5


SUPPORTED_FIELDS_BY_TYPE: dict[PlaylistType, frozenset[FieldName]] = {
    PlaylistType.ENGINE: frozenset({"title", "artist", "duration", "year", "bpm", "file_path"}),
    PlaylistType.REKORDBOX: frozenset({"title", "artist", "duration", "year", "bpm", "file_path"}),
    PlaylistType.SERATO: frozenset({"title", "artist", "year"}),
    PlaylistType.TRAKTOR: frozenset({"title", "artist", "duration", "year", "bpm"}),
    PlaylistType.VIRTUALDJ: frozenset({"title", "artist", "duration", "year", "bpm"}),
}


def sniff_csv(path: Path) -> PlaylistType:
    """Read the first header row of a CSV file and return its format."""
    with path.open(encoding="utf-8", newline="") as f:
        try:
            header = next(csv.reader(f))
        except StopIteration:
            raise UnknownFormatError(path) from None

    if header and "\ufeff" in header[0]:
        return PlaylistType.VIRTUALDJ
    if "#" in header:
        return PlaylistType.ENGINE
    if "name" in header:
        return PlaylistType.SERATO
    raise UnknownFormatError(path)


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
        self.require: frozenset[FieldName] = frozenset(require)  # type: ignore[arg-type]
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

    def stream(self) -> Iterator[Track]:
        """Route to the correct per-format streaming generator."""
        kw: dict[str, object] = {
            "require": self.require,
            "default_artist": self.default_artist,
        }
        detected_type = self.playlist_type
        unsupported = self.require - SUPPORTED_FIELDS_BY_TYPE.get(detected_type, frozenset())
        if unsupported:
            raise MissingFieldError(sorted(unsupported)[0])
        path_str = str(self.path)
        if detected_type == PlaylistType.ENGINE:
            yield from engine_iter(path_str, **kw)  # type: ignore[arg-type]
        elif detected_type == PlaylistType.REKORDBOX:
            yield from rekordbox_iter(path_str, **kw)  # type: ignore[arg-type]
        elif detected_type == PlaylistType.SERATO:
            yield from serato_iter(path_str, **kw)  # type: ignore[arg-type]
        elif detected_type == PlaylistType.TRAKTOR:
            yield from traktor_iter(path_str, **kw)  # type: ignore[arg-type]
        elif detected_type == PlaylistType.VIRTUALDJ:
            yield from virtualdj_iter(path_str, **kw)  # type: ignore[arg-type]
        else:
            raise UnknownFormatError(self.path)


__all__ = [
    "FieldName",
    "MalformedPlaylistError",
    "MissingFieldError",
    "PlaylistParser",
    "PlaylistParserError",
    "PlaylistType",
    "Track",
    "UnknownFormatError",
]

__version__ = "4.0.0"
