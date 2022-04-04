from csv import DictReader
from enum import IntEnum
from typing import Callable, List, Union

from .parsers.engine import parser as engine_parser
from .parsers.rekordbox import parser as rekordbox_parser
from .parsers.serato import parser as serato_parser
from .parsers.traktor import parser as traktor_parser
from .parsers.virtualdj import parser as virtualdj_parser
from .track import Track


class PlaylistType(IntEnum):
    UNKNOWN = 0
    ENGINE = 1
    REKORDBOX = 2
    SERATO = 3
    TRAKTOR = 4
    VIRTUALDJ = 5


class PlaylistParser(object):
    def __init__(
        self,
        file_path: str,
        *,
        require_title: bool = True,
        require_duration: bool = False,
        require_year: bool = False,
        require_bpm: bool = False,
        require_fp: bool = False,
        default_artist: str = "Unknown Artist",
        verbose: bool = False,
    ):
        self.file_path = file_path
        self.verbose = verbose
        self.playlist_type: PlaylistType = PlaylistType.UNKNOWN
        self.tracks: List[Track] = []
        self._parser: Union[Callable[[str], List], None] = None
        self.is_parsed = False
        self.require_title = require_title
        self.require_duration = require_duration
        self.require_bpm = require_bpm
        self.require_year = require_year
        self.require_fp = require_fp
        self.default_artist = default_artist

        self._determine_type()

    def _determine_type(self):
        if self.file_path.endswith(".nml"):
            if self.verbose:  # pragma: no cover
                print("Looking for nml")
            self._parser = traktor_parser
            self.playlist_type = PlaylistType.TRAKTOR
        elif self.file_path.endswith(".txt"):
            if self.verbose:  # pragma: no cover
                print("Looking for txt")
            self._parser = rekordbox_parser
            self.playlist_type = PlaylistType.REKORDBOX
        elif self.file_path.endswith(".csv"):
            if self.verbose:  # pragma: no cover
                print("Looking for csv. filepath: ", self.file_path)

            with open(self.file_path) as file:
                reader = DictReader(file)
                line = reader.__next__()
                if self.verbose:  # pragma: no cover
                    print("First line: ", line)

                if "\ufeffsep=" in line.keys():
                    self._parser = virtualdj_parser
                    self.playlist_type = PlaylistType.VIRTUALDJ

                if "#" in line.keys():
                    self._parser = engine_parser
                    self.playlist_type = PlaylistType.ENGINE

                if "name" in line.keys():
                    self._parser = serato_parser
                    self.playlist_type = PlaylistType.SERATO

        if self.verbose:  # pragma: no cover
            print(f"Initialized {self.playlist_type} playlist.")

        if self.playlist_type == PlaylistType.UNKNOWN:
            raise Exception(f"Couldn't determine playlist type from '{self.file_path}'")

    def parse(self):
        if self.verbose:  # pragma: no cover
            print("Parsing...")
        self.tracks = self._parser(
            self.file_path,
            require_title=self.require_title,  # type: ignore
            require_duration=self.require_duration,  # type: ignore
            require_bpm=self.require_bpm,  # type: ignore
            require_year=self.require_year,  # type: ignore
            require_fp=self.require_fp,  # type: ignore
            default_artist=self.default_artist,  # type: ignore
            verbose=self.verbose,  # type: ignore
        )  # type: ignore
        self.is_parsed = True
        if self.verbose:  # pragma: no cover
            print(f"Found {len(self.tracks)} tracks.")

    def get_tracks(self):
        if not self.is_parsed:
            self.parse()
        return self.tracks


__version__ = "3.0.0-beta.9"
