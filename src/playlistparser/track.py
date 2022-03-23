from datetime import timedelta
from typing import Dict, Union
from unicodedata import normalize


class Track(object):
    def __init__(
        self,
        *,
        title: str,
        artist: str,
        duration: int = 0,
        year: str = "",
        bpm: int = 0,
    ):
        self.title = normalize("NFC", title).strip()
        self.artist = normalize("NFC", artist).strip()
        self.duration = duration
        self.year = self._clean_year(year)
        self.bpm = bpm

    def __str__(self):
        return f"{self.artist} - {self.title}"

    def _clean_year(self, year: str):
        cleaned_year = year
        if "-" in year:
            cleaned_year = year.split("-")[0]
        elif "/" in year:
            cleaned_year = year.split("/")[0]
        else:
            cleaned_year = year
        try:
            return int(cleaned_year)
        except Exception:
            return 0

    def duration_str(self):
        if self.duration:
            string = str(timedelta(seconds=self.duration))

            # 0:00:12
            if string.startswith("0:"):
                string = string[2:]

            # 00:12
            if string.startswith("00:"):
                string = "0:" + string[3:]

            # 01:12
            if string.startswith("0") and not string.startswith("0:"):
                string = string[1:]
            return string
        else:
            return "0:00"

    def as_dict(self, no_meta=False):
        song: Dict[str, Union[str, int]] = {
            "title": self.title,
            "artist": self.artist,
        }
        if no_meta:
            return song
        if self.duration:
            song["duration"] = self.duration
            song["duration_str"] = self.duration_str()
        if self.year:
            song["year"] = self.year
        if self.bpm:
            song["bpm"] = self.bpm
        return song
