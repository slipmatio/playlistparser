from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser
from playlistparser.track import Track
from playlistparser.utils import time_str_to_seconds
from pytest import approx

ROOT_DIR = Path(__file__).resolve().parent.parent

ENGINE_FILE = join(ROOT_DIR, "data/enginedj-v21.csv")
REKORDBOX_FILE = join(ROOT_DIR, "data/rekordbox-v6.txt")
SERATO_FILE = join(ROOT_DIR, "data/serato-v25.csv")
TRAKTOR_FILE = join(ROOT_DIR, "data/traktor-v35.nml")
BROKEN_FILE = join(ROOT_DIR, "data/brokentestfile.dat")

verbose = False


def test_parser():
    with pytest.raises(Exception) as exc_info:
        PlaylistParser(BROKEN_FILE, verbose=verbose)
    assert str(exc_info.value).startswith("Unknown playlist type when opening")


def test_engine():
    parser = PlaylistParser(ENGINE_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 6
    assert "year" in track.as_dict().keys()


def test_rekordbox():
    parser = PlaylistParser(REKORDBOX_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 6
    assert "year" in track.as_dict().keys()


def test_serato():
    parser = PlaylistParser(SERATO_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 3
    assert "year" in track.as_dict().keys()


def test_traktor():
    parser = PlaylistParser(TRAKTOR_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 6
    assert "year" in track.as_dict().keys()


def test_all():
    en_parser = PlaylistParser(ENGINE_FILE, verbose=verbose)
    en_tracks = en_parser.get_tracks()
    en_song_0_dict = en_tracks[0].as_dict()

    rb_parser = PlaylistParser(REKORDBOX_FILE, verbose=verbose)
    rb_tracks = rb_parser.get_tracks()
    rb_song_0_dict = rb_tracks[0].as_dict()

    se_parser = PlaylistParser(SERATO_FILE, verbose=verbose)
    se_tracks = se_parser.get_tracks()
    se_song_0_dict = se_tracks[0].as_dict()

    tr_parser = PlaylistParser(TRAKTOR_FILE, verbose=verbose)
    tr_tracks = tr_parser.get_tracks()
    tr_song_0_dict = tr_tracks[0].as_dict()

    assert set(rb_song_0_dict.keys()).difference(set(en_song_0_dict.keys())) == set()
    assert set(rb_song_0_dict.keys()).difference(set(tr_song_0_dict.keys())) == set()
    assert set(en_song_0_dict.keys()).difference(set(se_song_0_dict.keys())) == set(
        {"bpm", "duration", "duration_str"}
    )

    assert len(rb_tracks) == len(en_tracks), "Rekordbox and Engine have different number of tracks"
    assert len(rb_tracks) == len(se_tracks), "Rekordbox and Serato have different number of tracks"

    assert len(en_song_0_dict.keys()) == len(
        rb_song_0_dict.keys()
    ), "Engine and Rekordbox have different keys"
    assert len(en_song_0_dict.keys()) == len(
        tr_song_0_dict.keys()
    ), "Engine and Traktor have different keys"

    for index, rb_song in enumerate(rb_tracks):
        en_song = en_tracks[index]
        se_song = se_tracks[index]
        tr_song = tr_tracks[index]

        assert rb_song.artist == en_song.artist == se_song.artist == tr_song.artist
        assert rb_song.title == en_song.title == se_song.title == tr_song.title
        assert rb_song.year == en_song.year == se_song.year == tr_song.year
        assert approx(rb_song.duration, abs=1) == en_song.duration
        assert approx(rb_song.duration, abs=1) == tr_song.duration


def test_utils():
    assert time_str_to_seconds("00:00:00") == 0
    assert time_str_to_seconds("00:00:10") == 10
    assert time_str_to_seconds("00:01:00") == 60
    assert time_str_to_seconds("00:10:00") == 600
    assert time_str_to_seconds("01:00:00") == 3600
    assert time_str_to_seconds("foo") == 0


def test_song_class():
    song = Track(title="test title", artist="test artist", year="2022", duration=10)
    assert song.title == "test title"
    assert song.year == 2022
    assert song.duration_str() == "0:10"
    assert str(song) == "test artist - test title"

    song = Track(title="test", artist="test", year="2022", duration=0)
    assert song.duration_str() == "0:00"

    song = Track(title="test", artist="test", year="2022-1-1", duration=60)
    assert song.duration_str() == "1:00"
    assert song.year == 2022

    song = Track(title="test", artist="test", year="2022/1/1", duration=360)
    assert song.duration_str() == "6:00"
    assert song.year == 2022

    song = Track(title="test", artist="test", year="2022/1/1", duration=3600)
    assert song.duration_str() == "1:00:00"

    song = Track(
        title="test",
        artist="test",
        year="2022/1/1",
        duration=2 * 3600 + 45 * 60 + 15,
        bpm=100,
    )
    assert song.duration_str() == "2:45:15"
    assert len(song.as_dict().keys()) == 6
    assert len(song.as_dict(no_meta=True).keys()) == 2
