import logging
from pathlib import Path

import pytest

import playlistparser as playlistparser_module
import playlistparser.parsers.engine as engine_parser
from playlistparser import (
    MissingFieldError,
    PlaylistParser,
    PlaylistType,
    UnknownFormatError,
)
from playlistparser.parsers.traktor import iter_tracks as original_traktor_iter
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


# PlaylistParser


@pytest.mark.parametrize(("file_path", "expected_type"), ALL_FORMAT_FILES)
def test_detect_format(file_path, expected_type):
    assert PlaylistParser(file_path).playlist_type == expected_type


def test_detect_format_unknown():
    with pytest.raises(UnknownFormatError) as exc_info:
        PlaylistParser(BROKEN_FILE)
    msg = str(exc_info.value)
    assert ".nml" in msg
    assert ".txt" in msg
    assert ".csv" in msg
    assert "as_type=" in msg


def test_detect_format_accepts_pathlib():
    assert PlaylistParser(Path(TRAKTOR_FILE)).playlist_type == PlaylistType.TRAKTOR


def test_detect_format_accepts_str():
    assert PlaylistParser(str(REKORDBOX_FILE)).playlist_type == PlaylistType.REKORDBOX


def test_parse_pathlib():
    tracks = PlaylistParser(Path(REKORDBOX_FILE)).to_list()
    assert len(tracks) == 4


def test_parse_str():
    tracks = PlaylistParser(str(TRAKTOR_FILE)).to_list()
    assert len(tracks) == 4


def test_parse_default_artist():
    tracks = PlaylistParser(ENGINE_FILE, default_artist="Unknown Artist").to_list()
    third = tracks[2]
    assert third.artist == "Unknown Artist"

    tracks2 = PlaylistParser(ENGINE_FILE, default_artist="Custom").to_list()
    assert tracks2[2].artist == "Custom"


def test_parse_format_override_uses_requested_parser_despite_extension(tmp_path):
    playlist = tmp_path / "engine-export.txt"
    playlist.write_bytes(ENGINE_FILE.read_bytes())

    tracks = PlaylistParser(playlist, as_type=PlaylistType.ENGINE).to_list()

    assert [track.title for track in tracks] == EXPECTED_TITLES


def test_iter_tracks_streams_without_validating_unconsumed_rows(tmp_path):
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


def test_playlist_accepts_str():
    p = PlaylistParser(str(REKORDBOX_FILE))
    assert len(p.to_list()) == 4


def test_playlist_accepts_pathlib():
    p = PlaylistParser(Path(TRAKTOR_FILE))
    assert len(p.to_list()) == 4


def test_playlist_path_property():
    p = PlaylistParser(REKORDBOX_FILE)
    assert isinstance(p.path, Path)
    assert p.path == Path(REKORDBOX_FILE)


def test_playlist_format_property():
    p = PlaylistParser(TRAKTOR_FILE)
    assert p.playlist_type == PlaylistType.TRAKTOR


def test_playlist_iter():
    p = PlaylistParser(ENGINE_FILE)
    tracks = list(p)
    assert len(tracks) == 4


def test_playlist_track_count():
    p = PlaylistParser(SERATO_FILE)
    assert p.track_count == 4


def test_playlist_tracks_lazy():
    p = PlaylistParser(ENGINE_FILE)
    # track_count triggers materialisation; verify it returns a positive int
    count = p.track_count
    assert count > 0
    # second to_list() returns the same cached list
    first = p.to_list()
    second = p.to_list()
    assert first is second


def test_playlist_format_override_uses_requested_parser_despite_extension(tmp_path):
    playlist = tmp_path / "rekordbox-export.csv"
    playlist.write_bytes(REKORDBOX_FILE.read_bytes())

    parser = PlaylistParser(playlist, as_type=PlaylistType.REKORDBOX)

    assert [track.title for track in parser.to_list()] == EXPECTED_TITLES


@pytest.mark.parametrize(("file_path", "expected_type"), ALL_FORMAT_FILES)
def test_playlist_detects_format(file_path, expected_type):
    p = PlaylistParser(file_path)
    assert p.playlist_type == expected_type


def test_playlist_unknown_raises():
    with pytest.raises(UnknownFormatError):
        PlaylistParser(BROKEN_FILE)


def test_broken_csv_raises_on_access():
    p = PlaylistParser(BROKEN_SERATO)
    with pytest.raises(UnknownFormatError):
        _ = p.to_list()


def test_unknown_error_message_lists_extensions():
    with pytest.raises(UnknownFormatError) as exc_info:
        PlaylistParser(BROKEN_FILE)
    msg = str(exc_info.value)
    assert ".nml" in msg
    assert ".csv" in msg
    assert "as_type=" in msg


def test_logger_receives_records(caplog, monkeypatch):
    """Skipped-row warnings are emitted via the parser's module logger."""

    def broken_track(**kwargs):
        del kwargs
        raise ValueError("forced track failure")

    monkeypatch.setattr(engine_parser, "Track", broken_track)
    with caplog.at_level(logging.DEBUG, logger=engine_parser.__name__):
        loaded = PlaylistParser(ENGINE_FILE).to_list()
    assert loaded == []
    assert any(
        record.name == engine_parser.__name__ and "forced track failure" in record.message for record in caplog.records
    )


# Cross-format consistency


def test_cross_format_track_data():
    """All formats yield the same title, artist, year for matching tracks."""
    rb_tracks = PlaylistParser(REKORDBOX_FILE).to_list()
    en_tracks = PlaylistParser(ENGINE_FILE).to_list()
    se_tracks = PlaylistParser(SERATO_FILE).to_list()
    tr_tracks = PlaylistParser(TRAKTOR_FILE).to_list()
    vj_tracks = PlaylistParser(VIRTUALDJ_FILE).to_list()

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
    tracks = PlaylistParser(DATA / "TestList100tracks.txt").to_list()
    assert len(tracks) == 100


def test_five_artists():
    tracks = PlaylistParser(DATA / "TestList5Artists.txt").to_list()
    artists = {t.artist for t in tracks}
    assert len(artists) == 5


# New PlaylistParser contract tests


def test_iter_makes_fresh_streaming_pass(monkeypatch):
    """Each for-loop over a PlaylistParser re-reads the file, never using the cache."""
    calls: list[int] = []

    def counting_iter(*args, **kwargs):
        calls.append(1)
        yield from original_traktor_iter(*args, **kwargs)

    monkeypatch.setattr(playlistparser_module, "traktor_iter", counting_iter)
    pl = PlaylistParser(TRAKTOR_FILE)

    first = list(pl)
    second = list(pl)

    assert first == second
    assert len(calls) == 2  # iter_tracks called twice — fresh pass each time


def test_to_list_uses_cache_on_second_call(monkeypatch):
    """to_list() populates the cache; a second call returns the same list object."""
    calls: list[int] = []

    def counting_iter(*args, **kwargs):
        calls.append(1)
        yield from original_traktor_iter(*args, **kwargs)

    monkeypatch.setattr(playlistparser_module, "traktor_iter", counting_iter)
    pl = PlaylistParser(TRAKTOR_FILE)

    first = pl.to_list()
    second = pl.to_list()

    assert first is second
    assert len(calls) == 1  # iter_tracks called only once


def test_track_count_and_total_duration_share_to_list_cache(monkeypatch):
    """track_count and total_duration reuse the cache populated by to_list()."""
    calls: list[int] = []

    def counting_iter(*args, **kwargs):
        calls.append(1)
        yield from original_traktor_iter(*args, **kwargs)

    monkeypatch.setattr(playlistparser_module, "traktor_iter", counting_iter)
    pl = PlaylistParser(TRAKTOR_FILE)

    tracks = pl.to_list()
    count = pl.track_count
    dur = pl.total_duration

    assert count == len(tracks)
    assert dur == sum(t.duration for t in tracks)
    assert len(calls) == 1  # only one file parse


def test_format_override_nonstandard_extension(tmp_path):
    """format= bypasses extension detection, allowing e.g. .dat to parse as ENGINE."""
    dat_file = tmp_path / "export.dat"
    dat_file.write_bytes(ENGINE_FILE.read_bytes())

    pl = PlaylistParser(dat_file, as_type=PlaylistType.ENGINE)
    tracks = pl.to_list()

    assert len(tracks) == 4
    assert [t.title for t in tracks] == EXPECTED_TITLES
