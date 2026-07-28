import logging
from pathlib import Path

import pytest

import playlistparser as playlistparser_module
import playlistparser.parsers.engine as engine_parser
from playlistparser import MissingFieldError, PlaylistParser, PlaylistType, UnknownFormatError
from playlistparser.parsers.traktor import iter_tracks as original_traktor_iter
from playlistparser.utils import time_str_to_seconds

DATA = Path(__file__).resolve().parent.parent / "data"

ENGINE_FILE = DATA / "enginedj-v21.csv"
REKORDBOX_FILE = DATA / "rekordbox-v6.txt"
SERATO_FILE = DATA / "serato-v25.csv"
TRAKTOR_FILE = DATA / "traktor-v35.nml"
VIRTUALDJ_FILE = DATA / "virtualdj-v2021.csv"
BROKEN_FILE = DATA / "brokentestfile.dat"

ALL_FORMAT_FILES = [
    (ENGINE_FILE, PlaylistType.ENGINE),
    (REKORDBOX_FILE, PlaylistType.REKORDBOX),
    (SERATO_FILE, PlaylistType.SERATO),
    (TRAKTOR_FILE, PlaylistType.TRAKTOR),
    (VIRTUALDJ_FILE, PlaylistType.VIRTUALDJ),
]


@pytest.mark.parametrize(
    ("raw", "seconds"),
    [
        ("00:00", 0),
        ("04:03", 243),
        ("160:36", 9636),
        ("00:00:10", 10),
        ("01:02:03", 3723),
        ("", 0),
        ("foo", 0),
    ],
)
def test_time_str_to_seconds(raw: str, seconds: int) -> None:
    assert time_str_to_seconds(raw) == seconds


@pytest.mark.parametrize(("file_path", "expected_type"), ALL_FORMAT_FILES)
def test_detect_format(file_path: Path, expected_type: PlaylistType) -> None:
    assert PlaylistParser(file_path).playlist_type == expected_type


def test_detect_format_unknown() -> None:
    with pytest.raises(UnknownFormatError) as error_info:
        PlaylistParser(BROKEN_FILE)

    message = str(error_info.value)
    assert ".nml" in message
    assert ".txt" in message
    assert ".csv" in message
    assert "as_type=" in message


def test_default_artist() -> None:
    tracks = PlaylistParser(ENGINE_FILE, default_artist="Custom").to_list()

    assert tracks[2].artist == "Custom"


def test_format_override(tmp_path: Path) -> None:
    playlist = tmp_path / "engine-export.txt"
    playlist.write_bytes(ENGINE_FILE.read_bytes())

    parser = PlaylistParser(playlist, as_type=PlaylistType.ENGINE)

    assert parser.playlist_type == PlaylistType.ENGINE
    assert len(parser.to_list()) == 4


def test_streaming_validation(tmp_path: Path) -> None:
    playlist = tmp_path / "streaming.csv"
    playlist.write_text(
        "#,Title,Artist,Length,BPM,Year,File name\n"
        '1,"First Track","Artist",60,120,2024,"/music/first.mp3"\n'
        '2,"","Artist",60,120,2024,"/music/broken.mp3"\n',
        encoding="utf-8",
    )
    tracks = iter(PlaylistParser(playlist, require=["title"]))

    assert next(tracks).title == "First Track"
    with pytest.raises(MissingFieldError):
        next(tracks)


def test_iteration_rereads_file(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def counting_iter(*args, **kwargs):
        calls.append(1)
        yield from original_traktor_iter(*args, **kwargs)

    monkeypatch.setattr(playlistparser_module, "traktor_iter", counting_iter)
    parser = PlaylistParser(TRAKTOR_FILE)

    assert list(parser) == list(parser)
    assert len(calls) == 2


def test_list_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def counting_iter(*args, **kwargs):
        calls.append(1)
        yield from original_traktor_iter(*args, **kwargs)

    monkeypatch.setattr(playlistparser_module, "traktor_iter", counting_iter)
    parser = PlaylistParser(TRAKTOR_FILE)

    tracks = parser.to_list()

    assert parser.to_list() is tracks
    assert parser.track_count == len(tracks)
    assert parser.total_duration == sum(track.duration for track in tracks)
    assert len(calls) == 1


def test_skipped_track_logging(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken_track(**kwargs: object) -> None:
        del kwargs
        raise ValueError("forced track failure")

    monkeypatch.setattr(engine_parser, "Track", broken_track)

    with caplog.at_level(logging.DEBUG, logger=engine_parser.__name__):
        loaded = PlaylistParser(ENGINE_FILE).to_list()

    assert loaded == []
    assert any(
        record.name == engine_parser.__name__ and "forced track failure" in record.message for record in caplog.records
    )
