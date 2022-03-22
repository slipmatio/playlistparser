import csv

from ..track import Track
from ..utils import time_str_to_seconds


def parser(file_path, *, verbose=False):
    """
    VirtualDJ supports:
    - title
    - artist
    - year
    - playtime
    - bpm
    """
    with open(file_path) as file:
        reader = csv.DictReader(
            file, fieldnames=["Title", "Artist", "Remix", "Length", "Bpm", "Key", "Year"]
        )
        tracks = []
        counter = 0

        for line in reader:
            if counter > 1:
                try:
                    title = line["Title"].strip()
                    artist = line["Artist"].strip()
                    playtime = time_str_to_seconds(line["Length"].strip())
                    bpm = int(float(line["Bpm"].strip()))
                    try:
                        year = line["Year"].strip()
                    except KeyError:
                        year = ""
                    tracks.append(
                        Track(title=title, artist=artist, year=year, duration=playtime, bpm=bpm)
                    )
                except Exception as e:  # pragma: no cover
                    if verbose:
                        print(f"Line {counter}: ", line)
                    print(f"Skipping line {counter}", e)

            counter += 1
        return tracks
