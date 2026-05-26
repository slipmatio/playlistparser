"""Tests for the Track dataclass."""

import dataclasses

import pytest

from playlistparser.track import Track


def test_basic_construction():
    t = Track(title="Test Title", artist="Test Artist", year="2022", duration=10)
    assert t.title == "Test Title"
    assert t.artist == "Test Artist"
    assert t.year == 2022
    assert t.duration == 10
    assert t.bpm == 0
    assert t.file_path == ""


def test_year_as_int():
    t = Track(title="x", artist="y", year=2022)
    assert t.year == 2022


def test_year_with_dashes():
    t = Track(title="x", artist="y", year="2022-01-01")
    assert t.year == 2022


def test_year_with_slashes():
    t = Track(title="x", artist="y", year="2022/01/01")
    assert t.year == 2022


def test_year_empty():
    t = Track(title="x", artist="y", year="")
    assert t.year == 0


def test_year_invalid():
    t = Track(title="x", artist="y", year="not-a-year")
    assert t.year == 0


# ---------------------------------------------------------------------------
# String normalisation
# ---------------------------------------------------------------------------


def test_title_stripped():
    t = Track(title="  test title  ", artist="a")
    assert t.title == "test title"


def test_artist_stripped():
    t = Track(title="t", artist="  test artist  ")
    assert t.artist == "test artist"


def test_nfc_normalisation_title():
    # e + combining acute vs precomposed é
    t1 = Track(title="test \u0065\u0301", artist="a")
    t2 = Track(title="test \u00e9", artist="a")
    assert t1.title == t2.title


def test_nfc_normalisation_artist():
    t1 = Track(title="t", artist="artist \u0065\u0301")
    t2 = Track(title="t", artist="artist \u00e9")
    assert t1.artist == t2.artist


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
    t = Track(title="x", artist="y", duration=seconds)
    assert t.duration_str() == expected


def test_str():
    t = Track(title="Title", artist="Artist")
    assert str(t) == "Artist - Title"


def test_equality():
    t1 = Track(title="Title", artist="Artist", year="2022", duration=10)
    t2 = Track(title="Title", artist="Artist", year="2022", duration=10)
    assert t1 == t2


def test_hash():
    t1 = Track(title="Title", artist="Artist", year="2022", duration=10)
    t2 = Track(title="Title", artist="Artist", year="2022", duration=10)
    assert hash(t1) == hash(t2)
    s = {t1, t2}
    assert len(s) == 1


def test_repr():
    t = Track(title="Title", artist="Artist", duration=10, year="2022")
    r = repr(t)
    assert "Title" in r
    assert "Artist" in r


def test_frozen():
    t = Track(title="x", artist="y")
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        t.title = "changed"  # type: ignore[invalid-assignment]  # ty:ignore[invalid-assignment]


def test_as_dict_full():
    t = Track(title="T", artist="A", year="2022", duration=60, bpm=130, file_path="/x.mp3")
    d = t.as_dict()
    assert d["title"] == "T"
    assert d["artist"] == "A"
    assert d["year"] == 2022
    assert d["duration"] == 60
    assert "duration_str" in d
    assert d["bpm"] == 130
    assert d["file_path"] == "/x.mp3"


def test_as_dict_minimal():
    """Fields that are falsy (0 / empty string) are omitted."""
    t = Track(title="T", artist="A")
    d = t.as_dict()
    assert set(d.keys()) == {"title", "artist"}


def test_as_dict_no_meta():
    t = Track(title="T", artist="A", year="2022", duration=60)
    d = t.as_dict(no_meta=True)
    assert set(d.keys()) == {"title", "artist"}


def test_as_dict_bpm_and_year():
    t = Track(title="T", artist="A", year="2022", duration=2 * 3600 + 45 * 60 + 15, bpm=100)
    assert t.as_dict() == {
        "title": "T",
        "artist": "A",
        "duration": 9915,
        "year": 2022,
        "bpm": 100,
        "duration_str": "2:45:15",
    }
