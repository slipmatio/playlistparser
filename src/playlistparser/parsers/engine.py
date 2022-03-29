import csv

from ..track import Track


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
    Engine supports:
    - title
    - artist
    - year
    - playtime
    - bpm
    - bpm
    - file_path
    """
    with open(file_path) as file:
        reader = csv.DictReader(file)
        tracks = []
        counter = 0

        for line in reader:
            try:
                title = line["Title"].strip()
                artist = line["Artist"].strip()
                if not artist:
                    artist = default_artist
                year = line["Year"].strip()
                bpm = int(line["BPM"].strip())
                playtime = int(line["Length"].strip())
                file_path = line["File name"].strip()
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
            except Exception as e:  # pragma: no cover
                print(f"Skipping line {counter}", e)

            counter += 1
        return tracks
