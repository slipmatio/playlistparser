import codecs
import csv
from io import StringIO

from ..track import Track
from ..utils import time_str_to_seconds


def parser(
    file_path,
    *,
    require_title=True,
    require_bpm=False,
    require_year=False,
    require_fp=False,
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
            title = ""
            artist = ""
            year = ""
            bpm = 0
            file_path = ""

            try:
                title = line["Track Title"].strip()
                artist = line["Artist"].strip()
                year = line["Year"].strip()
                bpm = int(float(line["BPM"].strip()))
                playtime = time_str_to_seconds(line["Time"].strip())
            except Exception as e:  # pragma: no cover
                print(f"Skipping line {counter}", e)
                continue

            try:
                file_path = line["Location"].strip()
            except Exception:
                if require_fp:
                    raise ValueError("File paths required but not found in file.")

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
