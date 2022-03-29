from csv import DictReader

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
    Serato supports:
    - title
    - artist
    - year
    """
    if require_duration:
        raise NotImplementedError("Serato parser doesn't support require_duration.")

    if require_year:
        raise NotImplementedError("Serato parser doesn't support require_year.")

    if require_bpm:
        raise NotImplementedError("Serato parser doesn't support require_bpm.")

    if require_fp:
        raise NotImplementedError("Serato parser doesn't support file paths.")

    with open(file_path) as file:
        reader = DictReader(file)
        tracks = []
        counter = 0

        for line in reader:
            if counter > 0:
                try:
                    title = line["name"].strip()
                    artist = line["artist"].strip()
                    if not artist:
                        artist = default_artist
                    year = line["year"].strip()
                    tracks.append(Track(title=title, artist=artist, year=year))
                except Exception as e:  # pragma: no cover
                    print(f"Skipping line {counter}", e)
            counter += 1
        return tracks
