from csv import DictReader
from typing import Callable, List, Union

from .parsers.engine import parser as engine_parser
from .parsers.rekordbox import parser as rekordbox_parser
from .parsers.serato import parser as serato_parser
from .parsers.traktor import parser as traktor_parser
from .parsers.virtualdj import parser as virtualdj_parser
from .track import Track


class PlaylistParser(object):
    def __init__(
        self,
        file_path=None,
        *,
        require_title=True,
        require_duration=False,
        require_year=False,
        require_bpm=False,
        require_fp=False,
        default_artist="Unknown Artist",
        verbose=False,
    ):
        self.file_path = file_path
        self.file_contents = None
        self.verbose = verbose
        self.playlist_type = "none"
        self.playlist_name = ""
        self.tracks: List[Track] = []
        self._parser: Union[Callable[[str], List], None] = None
        self.is_parsed = False
        self.require_title = require_title
        self.require_duration = require_duration
        self.require_bpm = require_bpm
        self.require_year = require_year
        self.require_fp = require_fp
        self.default_artist = default_artist

        self.playlist_type = self.get_playlist_type()
        if verbose:  # pragma: no cover
            print(f"Initialized {self.playlist_type} playlist.")

    def get_playlist_type(self):
        if self.file_path.endswith(".nml"):
            if self.verbose:  # pragma: no cover
                print("Looking for nml")
            self._parser = traktor_parser
            return "traktor"
        elif self.file_path.endswith(".txt"):
            if self.verbose:  # pragma: no cover
                print("Looking for txt")
            self._parser = rekordbox_parser
            return "rekordbox"
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
                    return "virtualdj"

                if "#" in line.keys():
                    self._parser = engine_parser
                    return "engine"

                if "name" in line.keys():
                    self._parser = serato_parser
                    return "serato"
        raise Exception(f"Unknown playlist type when opening {self.file_path} ")

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


__version__ = "3.0.0-beta.7"
