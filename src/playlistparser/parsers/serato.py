from csv import DictReader

from ..track import Track


def parser(file_path, *, verbose=False):
    """
    Serato supports:
    - title
    - artist
    - year
    """
    with open(file_path) as file:
        reader = DictReader(file)
        tracks = []
        counter = 0

        for line in reader:
            if counter > 0:
                try:
                    title = line["name"].strip()
                    artist = line["artist"].strip()
                    year = line["year"].strip()
                    tracks.append(Track(title=title, artist=artist, year=year))
                except Exception as e:  # pragma: no cover
                    print(f"Skipping line {counter}", e)
            counter += 1
        return tracks
