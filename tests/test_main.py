import logging
from pathlib import Path

import pytest

import playlistparser as pp
import playlistparser.parsers.engine as engine_parser
from playlistparser import (
    MissingFieldError,
    PlaylistParser,
    PlaylistType,
    UnknownFormatError,
)
from playlistparser.utils import time_str_to_seconds

DATA = Path(__file__).resolve().parent.parent / "data"

ENGINE_FILE = DATA / "enginedj-v21.csv"
REKORDBOX_FILE = DATA / "rekordbox-v6.txt"
SERATO_FILE = DATA / "serato-v25.csv"
TRAKTOR_FILE = DATA / "traktor-v35.nml"
VIRTUALDJ_FILE = DATA / "virtualdj-v2021.csv"
BROKEN_FILE = DATA / "brokentestfile.dat"
BROKEN_SERATO = DATA / "broken-serato-v25.csv"

ALL_FORMAT_FILES = [
    (ENGINE_FILE, PlaylistType.ENGINE),
    (REKORDBOX_FILE, PlaylistType.REKORDBOX),
    (SERATO_FILE, PlaylistType.SERATO),
    (TRAKTOR_FILE, PlaylistType.TRAKTOR),
    (VIRTUALDJ_FILE, PlaylistType.VIRTUALDJ),
]

EXPECTED_TITLES = [
    "Tähtikaaren Taa (2008 Remix)",
    "Taivas Lyö Tulta",
    "Orkidea - Luminosity Beach Festival 06-07-2014",
    "1998 (Paul Van Dyk Remix)",
]


# utils


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
def test_time_str_to_seconds(raw, seconds):
    assert time_str_to_seconds(raw) == seconds


# detect_format


@pytest.mark.parametrize("file_path,expected_type", ALL_FORMAT_FILES)
def test_detect_format(file_path, expected_type):
    assert pp.detect_format(file_path) == expected_type


def test_detect_format_unknown():
    with pytest.raises(UnknownFormatError) as exc_info:
        pp.detect_format(BROKEN_FILE)
    msg = str(exc_info.value)
    assert ".nml" in msg
    assert ".txt" in msg
    assert ".csv" in msg
    assert "as_type=" in msg


def test_detect_format_accepts_pathlib():
    assert pp.detect_format(Path(TRAKTOR_FILE)) == PlaylistType.TRAKTOR


def test_detect_format_accepts_str():
    assert pp.detect_format(str(REKORDBOX_FILE)) == PlaylistType.REKORDBOX


def test_parse_pathlib():
    tracks = pp.parse(Path(REKORDBOX_FILE))
    assert len(tracks) == 4


def test_parse_str():
    tracks = pp.parse(str(TRAKTOR_FILE))
    assert len(tracks) == 4


def test_parse_default_artist():
    tracks = pp.parse(ENGINE_FILE, default_artist="Unknown Artist")
    third = tracks[2]
    assert third.artist == "Unknown Artist"

    tracks2 = pp.parse(ENGINE_FILE, default_artist="Custom")
    assert tracks2[2].artist == "Custom"


def test_parse_format_override_uses_requested_parser_despite_extension(tmp_path):
    playlist = tmp_path / "engine-export.txt"
    playlist.write_bytes(ENGINE_FILE.read_bytes())

    tracks = pp.parse(playlist, as_type=PlaylistType.ENGINE)

    assert [track.title for track in tracks] == EXPECTED_TITLES


def test_iter_tracks_streams_without_validating_unconsumed_rows(tmp_path):
    playlist = tmp_path / "streaming.csv"
    playlist.write_text(
        "#,Title,Artist,Length,BPM,Year,File name\n"
        '1,"First Track","Artist",60,120,2024,"/music/first.mp3"\n'
        '2,"","Artist",60,120,2024,"/music/broken.mp3"\n',
        encoding="utf-8",
    )

    tracks = pp.iter_tracks(playlist, require=["title"])

    assert next(tracks).title == "First Track"
    with pytest.raises(MissingFieldError):
        next(tracks)


# PlaylistParser


def test_playlist_parser_accepts_str():
    p = PlaylistParser(str(REKORDBOX_FILE))
    assert len(p.tracks) == 4


def test_playlist_parser_accepts_pathlib():
    p = PlaylistParser(Path(TRAKTOR_FILE))
    assert len(p.tracks) == 4


def test_playlist_parser_path_property():
    p = PlaylistParser(REKORDBOX_FILE)
    assert isinstance(p.path, Path)
    assert p.path == Path(REKORDBOX_FILE)


def test_playlist_parser_format_property():
    p = PlaylistParser(TRAKTOR_FILE)
    assert p.as_type == PlaylistType.TRAKTOR
    assert p.playlist_type == PlaylistType.TRAKTOR


def test_playlist_parser_iter():
    p = PlaylistParser(ENGINE_FILE)
    tracks = list(p)
    assert len(tracks) == 4


def test_playlist_parser_len():
    p = PlaylistParser(SERATO_FILE)
    assert len(p) == 4


def test_playlist_parser_tracks_lazy():
    p = PlaylistParser(ENGINE_FILE)
    assert p.cached_tracks is None  # not yet materialised
    tracks = p.tracks  # trigger lazy load
    assert len(tracks) > 0
    assert p.cached_tracks is not None


def test_playlist_parser_format_override_uses_requested_parser_despite_extension(tmp_path):
    playlist = tmp_path / "rekordbox-export.csv"
    playlist.write_bytes(REKORDBOX_FILE.read_bytes())

    parser = PlaylistParser(playlist, as_type=PlaylistType.REKORDBOX)

    assert [track.title for track in parser.tracks] == EXPECTED_TITLES


@pytest.mark.parametrize("file_path,expected_type", ALL_FORMAT_FILES)
def test_playlist_parser_detects_format(file_path, expected_type):
    p = PlaylistParser(file_path)
    assert p.playlist_type == expected_type


def test_playlist_parser_unknown_raises():
    with pytest.raises(UnknownFormatError):
        PlaylistParser(BROKEN_FILE)


def test_broken_csv_raises_on_access():
    p = PlaylistParser(BROKEN_SERATO)
    with pytest.raises(UnknownFormatError):
        _ = p.tracks


def test_unknown_error_message_lists_extensions():
    with pytest.raises(UnknownFormatError) as exc_info:
        PlaylistParser(BROKEN_FILE)
    msg = str(exc_info.value)
    assert ".nml" in msg
    assert ".csv" in msg
    assert "as_type=" in msg


# logger= parameter


def test_logger_receives_records(caplog, monkeypatch):
    """A caller-supplied logger= should receive debug records for skipped rows."""

    def broken_track(**kwargs):
        del kwargs
        raise ValueError("forced track failure")

    monkeypatch.setattr(engine_parser, "Track", broken_track)
    custom_logger = logging.getLogger("test_custom")
    with caplog.at_level(logging.DEBUG, logger="test_custom"):
        p = PlaylistParser(ENGINE_FILE, logger=custom_logger)
        loaded = p.tracks
    assert loaded == []
    assert p.cached_tracks is not None
    assert any(record.name == "test_custom" and "forced track failure" in record.message for record in caplog.records)


# Cross-format consistency


def test_cross_format_track_data():
    """All formats yield the same title, artist, year for matching tracks."""
    rb_tracks = pp.parse(REKORDBOX_FILE)
    en_tracks = pp.parse(ENGINE_FILE)
    se_tracks = pp.parse(SERATO_FILE)
    tr_tracks = pp.parse(TRAKTOR_FILE)
    vj_tracks = pp.parse(VIRTUALDJ_FILE)

    assert len(rb_tracks) == len(en_tracks) == len(se_tracks) == len(tr_tracks) == len(vj_tracks)

    for i, rb in enumerate(rb_tracks):
        en = en_tracks[i]
        se = se_tracks[i]
        tr = tr_tracks[i]
        vj = vj_tracks[i]
        assert rb.artist == en.artist == se.artist == tr.artist == vj.artist
        assert rb.title == en.title == se.title == tr.title == vj.title
        assert rb.year == en.year == se.year == tr.year == vj.year


def test_num_tracks_large_file():
    tracks = pp.parse(DATA / "TestList100tracks.txt")
    assert len(tracks) == 100


def test_five_artists():
    tracks = pp.parse(DATA / "TestList5Artists.txt")
    artists = {t.artist for t in tracks}
    assert len(artists) == 5
