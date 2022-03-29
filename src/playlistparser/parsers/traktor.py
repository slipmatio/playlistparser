import xml.etree.ElementTree as ET

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
    Traktor supports:
    - title
    - artist
    - year
    - playtime
    - bpm
    """
    if require_fp:
        raise NotImplementedError("Traktor parser doesn't support file paths.")

    tracks = []
    traktor_xml = ""
    counter = 0

    with open(file_path) as file:
        traktor_xml = ET.fromstring(file.read())

    entries = traktor_xml.findall("COLLECTION/ENTRY")

    for track in entries:
        playtime = 0
        year = ""
        bpm = 0

        try:
            track_title = track.get("TITLE", "").strip()
            track_artist = track.get("ARTIST", "").strip()
            if not track_artist:
                track_artist = default_artist

            meta = track.find("INFO")
            if meta is not None:
                playtime = int(meta.get("PLAYTIME", ""))
                # key = meta.get("KEY", "")
                year = meta.get("RELEASE_DATE", "")
                if verbose:  # pragma: no cover
                    print(f"found year: {year}, playtime: {playtime}")

            tempometa = track.find("TEMPO")
            if tempometa is not None:
                bpm = int(float(tempometa.get("BPM", 0)))

            tracks.append(
                Track(
                    title=track_title,
                    artist=track_artist,
                    year=year,
                    duration=playtime,
                    bpm=bpm,
                )
            )
        except Exception as e:  # pragma: no cover
            print(f"Skipping line {counter}", e)

        counter += 1

    return tracks
