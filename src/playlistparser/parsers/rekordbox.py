import codecs
import csv
from io import StringIO

from ..track import Track
from ..utils import time_str_to_seconds


def parser(
    file_path,
    *,
    require_title=True,
    require_duration=False,
    require_year=False,
    require_bpm=False,
    require_fp=False,
    default_artist="",
    verbose=False,
):
    """
    Rekordbox supports:
    - title
    - artist
    - year
    - playtime
    - bpm
    - file_path
    """
    with open(file_path, "rb") as handle, codecs.EncodedFile(
        handle, data_encoding="utf-8", file_encoding="utf-16", errors="ignore"
    ) as stream:

        reader = csv.DictReader(StringIO(stream.read().decode("utf-8")), delimiter="\t")  # type: ignore

        tracks = []
        counter = 0

        for line in reader:
            artist = ""
            title = "Unknown"
            playtime = 0
            year = ""
            bpm = 0
            file_path = ""

            try:
                title = line["Track Title"].strip()
            except KeyError:
                if require_title:
                    raise ValueError("Title required but not found in file.")

            try:
                playtime = time_str_to_seconds(line["Time"].strip())
            except KeyError:
                if require_duration:
                    raise ValueError("Duration required but not found in file.")

            try:
                bpm = int(float(line["BPM"].strip()))
            except KeyError:
                if require_bpm:
                    raise ValueError("BPM required but not found in file.")

            try:
                year = line["Year"].strip()
            except KeyError:
                if require_year:
                    raise ValueError("Year required but not found in file.")

            try:
                file_path = line["Location"].strip()
            except Exception:
                if require_fp:
                    raise ValueError("File paths required but not found in file.")

            artist = line["Artist"].strip()
            if not artist:
                artist = default_artist

            tracks.append(
                Track(
                    title=title,
                    artist=artist,
                    year=year,
                    duration=playtime,
                    bpm=bpm,
                    file_path=file_path,
                )
            )
            counter += 1
        return tracks
