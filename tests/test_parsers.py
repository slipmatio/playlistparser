import csv
from pathlib import Path

import pytest

from playlistparser import FieldName, MissingFieldError, PlaylistParser

DATA = Path(__file__).resolve().parent.parent / "data"

ENGINE_FILE = DATA / "enginedj-v21.csv"
REKORDBOX_FILE = DATA / "rekordbox-v6.txt"
SERATO_FILE = DATA / "serato-v25.csv"
TRAKTOR_FILE = DATA / "traktor-v35.nml"
VIRTUALDJ_FILE = DATA / "virtualdj-v2021.csv"


@pytest.mark.parametrize(
    ("title", "artist", "track_path", "expected_artist", "expected_title"),
    [
        (
            "History Artist - Track - Club Mix",
            "",
            "/music/track.mp3.temp#history#event.temp",
            "History Artist",
            "Track - Club Mix",
        ),
        (
            "Title containing - a separator",
            "Tagged Artist",
            "/music/track.mp3.temp#history#event.temp",
            "Tagged Artist",
            "Title containing - a separator",
        ),
        (
            "Title containing - a separator",
            "",
            "/music/track.mp3",
            "Fallback Artist",
            "Title containing - a separator",
        ),
        (
            "Unsplittable title",
            "",
            "/music/track.mp3.temp#history#event.temp",
            "Fallback Artist",
            "Unsplittable title",
        ),
    ],
)
def test_engine_history_metadata_resolution(
    tmp_path: Path,
    title: str,
    artist: str,
    track_path: str,
    expected_artist: str,
    expected_title: str,
) -> None:
    playlist = tmp_path / "history.csv"
    with playlist.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["#", "Title", "Artist", "Length", "BPM", "Year", "File name"])
        writer.writerow([1, title, artist, 60, 120, 2026, track_path])

    track = PlaylistParser(playlist, default_artist="Fallback Artist").to_list()[0]

    assert (track.artist, track.title) == (expected_artist, expected_title)


@pytest.mark.parametrize(
    (
        "file_path",
        "track_index",
        "expected_album",
        "expected_key",
        "expected_bpm",
        "expected_path",
        "expected_vendor_state",
    ),
    [
        (
            ENGINE_FILE,
            0,
            "Greatest Hits",
            "",
            130.0,
            "/Volumes/Sammy/iTunes/iTunes Music/Music/Aikakone/Greatest Hits/2-05 Tähtikaaren Taa (2008 Remix).mp3",
            "empty",
        ),
        (
            REKORDBOX_FILE,
            3,
            "1998 (Single)",
            "Bm",
            137.5,
            "/Volumes/Sammy/iTunes/iTunes Music/Music/Binary Finary/1998 (Single)/02 1998 (Paul Van Dyk Remix).mp3",
            "empty",
        ),
        (SERATO_FILE, 0, "", "", 0.0, "", "empty"),
        (
            TRAKTOR_FILE,
            3,
            "1998 (Single)",
            "Bm",
            137.7,
            "/Users/uninen/Documents/02 1998 (Paul Van Dyk Remix).mp3",
            "present",
        ),
        (VIRTUALDJ_FILE, 2, "", "F", 137.9, "", "empty"),
    ],
)
def test_source_metadata(
    file_path: Path,
    track_index: int,
    expected_album: str,
    expected_key: str,
    expected_bpm: float,
    expected_path: str,
    expected_vendor_state: str,
) -> None:
    track = PlaylistParser(file_path).to_list()[track_index]

    assert track.album == expected_album
    assert track.key == expected_key
    assert track.bpm == expected_bpm
    assert track.file_path == expected_path
    vendor_state = "present" if track.vendor_id else "empty"
    assert vendor_state == expected_vendor_state


@pytest.mark.parametrize(
    ("file_path", "required_field"),
    [
        (DATA / "rekordbox-v6-missing-meta.txt", "title"),
        (DATA / "rekordbox-v6-missing-meta.txt", "duration"),
        (DATA / "rekordbox-v6-missing-meta.txt", "bpm"),
        (DATA / "PlaylistConverterTest-wo-year.txt", "year"),
        (DATA / "rekordbox_1.txt", "file_path"),
        (SERATO_FILE, "duration"),
        (SERATO_FILE, "bpm"),
        (SERATO_FILE, "file_path"),
        (VIRTUALDJ_FILE, "file_path"),
    ],
)
def test_required_field(file_path: Path, required_field: FieldName) -> None:
    with pytest.raises(MissingFieldError) as error_info:
        PlaylistParser(file_path, require=[required_field]).to_list()

    assert error_info.value.field == required_field
