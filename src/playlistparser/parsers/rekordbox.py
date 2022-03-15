import codecs
import csv
from io import StringIO

from ..track import Track
from ..utils import time_str_to_seconds


def parser(file_path, *, verbose=False):
    """
    Rekordbox supports:
    - title
    - artist
    - year
    - playtime
    - bpm
    """
    with open(file_path, "rb") as handle, codecs.EncodedFile(
        handle, data_encoding="utf-8", file_encoding="utf-16", errors="ignore"
    ) as stream:

        reader = csv.DictReader(StringIO(stream.read().decode("utf-8")), delimiter="\t")  # type: ignore

        tracks = []
        counter = 0

        for line in reader:
            try:
                title = line["Track Title"].strip()
                artist = line["Artist"].strip()
                year = line["Year"].strip()
                bpm = int(float(line["BPM"].strip()))
                playtime = time_str_to_seconds(line["Time"].strip())
                tracks.append(
                    Track(title=title, artist=artist, year=year, duration=playtime, bpm=bpm)
                )
            except Exception as e:  # pragma: no cover
                print(f"Skipping line {counter}", e)

            counter += 1
        return tracks
