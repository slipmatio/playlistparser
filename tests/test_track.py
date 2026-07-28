import pytest

from playlistparser.track import Track


@pytest.mark.parametrize(
    ("raw_year", "expected_year"),
    [
        (2022, 2022),
        ("2022-01-01", 2022),
        ("2022/01/01", 2022),
        ("", 0),
        ("not-a-year", 0),
    ],
)
def test_year_normalization(raw_year: str | int, expected_year: int) -> None:
    assert Track(title="Title", artist="Artist", year=raw_year).year == expected_year


def test_text_normalization() -> None:
    first = Track(title="  test \u0065\u0301  ", artist="  artist \u0065\u0301  ", album="  album \u0065\u0301  ")
    second = Track(title="test \u00e9", artist="artist \u00e9", album="album \u00e9")

    assert first.title == second.title
    assert first.artist == second.artist
    assert first.album == second.album


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
def test_duration_str(seconds: int, expected: str) -> None:
    assert Track(title="Title", artist="Artist", duration=seconds).duration_str() == expected


def test_as_dict_contract() -> None:
    track = Track(
        title="Title",
        artist="Artist",
        album="Album",
        key="8A",
        year="2022",
        duration=60,
        bpm=130.04,
        file_path="/x.mp3",
        vendor_id="vendor-1",
    )

    assert track.as_dict() == {
        "title": "Title",
        "artist": "Artist",
        "album": "Album",
        "key": "8A",
        "duration": 60,
        "year": 2022,
        "bpm": 130.0,
        "file_path": "/x.mp3",
        "vendor_id": "vendor-1",
        "duration_str": "1:00",
    }
    assert track.as_dict(no_meta=True) == {"title": "Title", "artist": "Artist"}
    assert Track(title="Title", artist="Artist").as_dict() == {"title": "Title", "artist": "Artist"}
