"""Tests for the Track dataclass."""

import dataclasses

import pytest

from playlistparser.track import Track


def test_basic_construction():
    track = Track(title="Test Title", artist="Test Artist", year="2022", duration=10)
    assert track.title == "Test Title"
    assert track.artist == "Test Artist"
    assert track.year == 2022
    assert track.duration == 10
    assert track.bpm == 0
    assert track.file_path == ""


def test_year_as_int():
    track = Track(title="x", artist="y", year=2022)
    assert track.year == 2022


def test_year_with_dashes():
    track = Track(title="x", artist="y", year="2022-01-01")
    assert track.year == 2022


def test_year_with_slashes():
    track = Track(title="x", artist="y", year="2022/01/01")
    assert track.year == 2022


def test_year_empty():
    track = Track(title="x", artist="y", year="")
    assert track.year == 0


def test_year_invalid():
    track = Track(title="x", artist="y", year="not-a-year")
    assert track.year == 0


# ---------------------------------------------------------------------------
# String normalisation
# ---------------------------------------------------------------------------


def test_title_stripped():
    track = Track(title="  test title  ", artist="a")
    assert track.title == "test title"


def test_artist_stripped():
    track = Track(title="t", artist="  test artist  ")
    assert track.artist == "test artist"


def test_nfc_normalisation_title():
    # e + combining acute vs precomposed é
    track1 = Track(title="test \u0065\u0301", artist="a")
    track2 = Track(title="test \u00e9", artist="a")
    assert track1.title == track2.title


def test_nfc_normalisation_artist():
    track1 = Track(title="t", artist="artist \u0065\u0301")
    track2 = Track(title="t", artist="artist \u00e9")
    assert track1.artist == track2.artist


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "0:00"),
        (10, "0:10"),
        (60, "1:00"),
        (360, "6:00"),
        (3600, "1:00:00"),
        (2 * 3600 + 45 * 60 + 15, "2:45:15"),
    ],
)
def test_duration_str(seconds, expected):
    track = Track(title="x", artist="y", duration=seconds)
    assert track.duration_str() == expected


def test_str():
    track = Track(title="Title", artist="Artist")
    assert str(track) == "Artist - Title"


def test_equality():
    track1 = Track(title="Title", artist="Artist", year="2022", duration=10)
    track2 = Track(title="Title", artist="Artist", year="2022", duration=10)
    assert track1 == track2


def test_hash():
    track1 = Track(title="Title", artist="Artist", year="2022", duration=10)
    track2 = Track(title="Title", artist="Artist", year="2022", duration=10)
    assert hash(track1) == hash(track2)
    unique_tracks = {track1, track2}
    assert len(unique_tracks) == 1


def test_repr():
    track = Track(title="Title", artist="Artist", duration=10, year="2022")
    r = repr(track)
    assert "Title" in r
    assert "Artist" in r


def test_frozen():
    track = Track(title="x", artist="y")
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        track.title = "changed"  # type: ignore[invalid-assignment]  # ty:ignore[invalid-assignment]


def test_as_dict_full():
    track = Track(title="T", artist="A", year="2022", duration=60, bpm=130, file_path="/x.mp3")
    d = track.as_dict()
    assert d["title"] == "T"
    assert d["artist"] == "A"
    assert d["year"] == 2022
    assert d["duration"] == 60
    assert "duration_str" in d
    assert d["bpm"] == 130
    assert d["file_path"] == "/x.mp3"


def test_as_dict_minimal():
    """Fields that are falsy (0 / empty string) are omitted."""
    track = Track(title="T", artist="A")
    d = track.as_dict()
    assert set(d.keys()) == {"title", "artist"}


def test_as_dict_no_meta():
    track = Track(title="T", artist="A", year="2022", duration=60)
    d = track.as_dict(no_meta=True)
    assert set(d.keys()) == {"title", "artist"}


def test_as_dict_bpm_and_year():
    track = Track(title="T", artist="A", year="2022", duration=2 * 3600 + 45 * 60 + 15, bpm=100)
    assert track.as_dict() == {
        "title": "T",
        "artist": "A",
        "duration": 9915,
        "year": 2022,
        "bpm": 100,
        "duration_str": "2:45:15",
    }
