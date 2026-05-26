"""playlistparser — public API."""

import csv
import logging
import os
from collections.abc import Iterable, Iterator
from enum import IntEnum
from pathlib import Path
from typing import Literal

from .exceptions import MalformedPlaylistError, MissingFieldError, PlaylistParserError, UnknownFormatError
from .parsers.engine import iter_tracks as engine_iter
from .parsers.rekordbox import iter_tracks as rekordbox_iter
from .parsers.serato import iter_tracks as serato_iter
from .parsers.traktor import iter_tracks as traktor_iter
from .parsers.virtualdj import iter_tracks as virtualdj_iter
from .track import Track

# ---------------------------------------------------------------------------
# Public type aliases
# ---------------------------------------------------------------------------

FieldName = Literal["title", "artist", "duration", "year", "bpm", "file_path"]

# ---------------------------------------------------------------------------
# PlaylistType enum
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Format detection helpers
# ---------------------------------------------------------------------------


def sniff_csv(path: Path) -> PlaylistType:
    """Read the first header row of a CSV file and return its format."""
    with open(path, encoding="utf-8", newline="") as f:
        try:
            header = next(csv.reader(f))
        except StopIteration:
            raise UnknownFormatError(path) from None

    if header and "\ufeff" in header[0]:
        return PlaylistType.VIRTUALDJ
    elif "#" in header:
        return PlaylistType.ENGINE
    elif "name" in header:
        return PlaylistType.SERATO
    else:
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


# ---------------------------------------------------------------------------
# PlaylistParser
# ---------------------------------------------------------------------------


class PlaylistParser:
    """Parse a DJ playlist file.

    Accepts a ``str`` or :class:`os.PathLike` path.  Format detection is
    lazy for CSV files (no I/O in the constructor).

    Example::

        parser = PlaylistParser("set.nml", require=["title", "year"])
        for track in parser:
            print(track)
        print(len(parser))  # materialises if not yet iterated
        print(parser.tracks[0])  # lazy property
    """

    def __init__(
        self,
        file_path: str | os.PathLike[str],
        *,
        require: Iterable[FieldName] = (),
        as_type: PlaylistType | None = None,
        logger: logging.Logger | None = None,
        default_artist: str = "Unknown Artist",
    ):
        self.path = Path(os.fspath(file_path))
        self.logger = logger or logging.getLogger(__name__)
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

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def as_type(self) -> PlaylistType:
        """Detected playlist format (alias for :attr:`playlist_type`)."""
        return self.playlist_type

    @property
    def playlist_type(self) -> PlaylistType:
        """Format of the playlist, detected lazily for CSV files."""
        if self.resolved_type is None:
            self.resolved_type = sniff_csv(self.path)
        return self.resolved_type

    @property
    def tracks(self) -> list[Track]:
        """All tracks, materialised lazily on first access."""
        if self.cached_tracks is None:
            self.cached_tracks = list(self.stream())
        return self.cached_tracks

    # ------------------------------------------------------------------
    # Iteration / sizing
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[Track]:
        """Yield tracks one by one without materialising the whole list."""
        yield from self.stream()

    def __len__(self) -> int:
        """Total number of tracks (materialises if not yet accessed)."""
        return len(self.tracks)

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def stream(self) -> Iterator[Track]:
        """Route to the correct per-format streaming generator."""
        kw: dict[str, object] = {
            "require": self.require,
            "default_artist": self.default_artist,
            "logger": self.logger,
        }
        pt = self.playlist_type
        unsupported = self.require - SUPPORTED_FIELDS_BY_TYPE.get(pt, frozenset())
        if unsupported:
            raise MissingFieldError(sorted(unsupported)[0])
        path_str = str(self.path)
        if pt == PlaylistType.ENGINE:
            yield from engine_iter(path_str, **kw)  # type: ignore[arg-type]
        elif pt == PlaylistType.REKORDBOX:
            yield from rekordbox_iter(path_str, **kw)  # type: ignore[arg-type]
        elif pt == PlaylistType.SERATO:
            yield from serato_iter(path_str, **kw)  # type: ignore[arg-type]
        elif pt == PlaylistType.TRAKTOR:
            yield from traktor_iter(path_str, **kw)  # type: ignore[arg-type]
        elif pt == PlaylistType.VIRTUALDJ:
            yield from virtualdj_iter(path_str, **kw)  # type: ignore[arg-type]
        else:
            raise UnknownFormatError(self.path)


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def detect_format(path: str | os.PathLike[str]) -> PlaylistType:
    """Detect and return the :class:`PlaylistType` for *path*."""
    return resolve_format(Path(os.fspath(path)))


def iter_tracks(
    path: str | os.PathLike[str],
    *,
    require: Iterable[FieldName] = (),
    default_artist: str = "Unknown Artist",
    as_type: PlaylistType | None = None,
    logger: logging.Logger | None = None,
) -> Iterator[Track]:
    """Stream tracks from *path* without materialising the full list.

    Example::

        for track in iter_tracks("massive.nml"):
            process(track)
    """
    yield from PlaylistParser(
        path,
        require=require,
        default_artist=default_artist,
        as_type=as_type,
        logger=logger,
    )


def parse(
    path: str | os.PathLike[str],
    *,
    require: Iterable[FieldName] = (),
    default_artist: str = "Unknown Artist",
    as_type: PlaylistType | None = None,
    logger: logging.Logger | None = None,
) -> list[Track]:
    """Parse *path* and return all tracks as a list.

    Example::

        tracks = parse("set.csv", require=["title", "year"])
    """
    return list(
        iter_tracks(
            path,
            require=require,
            default_artist=default_artist,
            as_type=as_type,
            logger=logger,
        )
    )


# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------

__all__ = [
    "FieldName",
    "MalformedPlaylistError",
    "MissingFieldError",
    "PlaylistParser",
    "PlaylistParserError",
    "PlaylistType",
    "Track",
    "UnknownFormatError",
    "detect_format",
    "iter_tracks",
    "parse",
]

__version__ = "4.0.0"
