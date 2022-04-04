from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser, PlaylistType
from pytest import approx

ROOT_DIR = Path(__file__).resolve().parent.parent

ENGINE_FILE = join(ROOT_DIR, "data/enginedj-v21.csv")
REKORDBOX_FILE = join(ROOT_DIR, "data/rekordbox-v6.txt")
SERATO_FILE = join(ROOT_DIR, "data/serato-v25.csv")
TRAKTOR_FILE = join(ROOT_DIR, "data/traktor-v35.nml")
VIRTUALDJ_FILE = join(ROOT_DIR, "data/virtualdj-v2021.csv")
BROKEN_FILE = join(ROOT_DIR, "data/brokentestfile.dat")
BROKEN_SERATO = join(ROOT_DIR, "data/broken-serato-v25.csv")

verbose = False


def test_broken_files():
    with pytest.raises(Exception) as exc_info:
        PlaylistParser(BROKEN_FILE, verbose=verbose)
    assert str(exc_info.value).startswith("Couldn't determine playlist type")

    with pytest.raises(Exception) as exc_info:
        PlaylistParser(BROKEN_SERATO, verbose=verbose)
    assert str(exc_info.value).startswith("Couldn't determine playlist type")


def test_engine():
    parser = PlaylistParser(ENGINE_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 7
    assert "year" in track.as_dict().keys()
    assert tracks[2].artist == "Unknown Artist"
    assert parser.playlist_type == PlaylistType.ENGINE


def test_rekordbox():
    parser = PlaylistParser(REKORDBOX_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 7
    assert "year" in track.as_dict().keys()
    assert tracks[2].artist == "Unknown Artist"
    assert parser.playlist_type == PlaylistType.REKORDBOX


def test_serato():
    parser = PlaylistParser(SERATO_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 3
    assert "year" in track.as_dict().keys()
    assert tracks[2].artist == "Unknown Artist"


def test_traktor():
    parser = PlaylistParser(TRAKTOR_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 6
    assert "year" in track.as_dict().keys()
    assert tracks[2].artist == "Unknown Artist"
    assert parser.playlist_type == PlaylistType.TRAKTOR


def test_virtualdj():
    parser = PlaylistParser(VIRTUALDJ_FILE, verbose=verbose)
    tracks = parser.get_tracks()
    track = tracks[0]
    assert len(tracks) == 4
    assert len(track.as_dict().keys()) == 6
    assert "year" in track.as_dict().keys()
    assert tracks[2].artist == "Unknown Artist"
    assert parser.playlist_type == PlaylistType.VIRTUALDJ


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

    vr_parser = PlaylistParser(VIRTUALDJ_FILE, verbose=verbose)
    vr_tracks = vr_parser.get_tracks()
    vr_song_0_dict = vr_tracks[0].as_dict()

    assert (
        set(rb_song_0_dict.keys()).difference(set(en_song_0_dict.keys())) == set()
    ), "Rekordbox keys should be identical to Engine keys"
    assert set(rb_song_0_dict.keys()).difference(set(tr_song_0_dict.keys())) == set({"file_path"})
    assert set(rb_song_0_dict.keys()).difference(set(vr_song_0_dict.keys())) == set({"file_path"})
    assert set(en_song_0_dict.keys()).difference(set(se_song_0_dict.keys())) == set(
        {"bpm", "duration", "duration_str", "file_path"}
    )

    assert len(rb_tracks) == len(en_tracks), "Rekordbox and Engine have different number of tracks"
    assert len(rb_tracks) == len(se_tracks), "Rekordbox and Serato have different number of tracks"
    assert len(rb_tracks) == len(
        vr_tracks
    ), "Rekordbox and VirtualDJ have different number of tracks"

    assert len(en_song_0_dict.keys()) == len(
        rb_song_0_dict.keys()
    ), "Engine and Rekordbox have different keys"
    # assert len(en_song_0_dict.keys()) == len(
    #     tr_song_0_dict.keys()
    # ), "Engine and Traktor have different keys"
    # assert len(en_song_0_dict.keys()) == len(
    #     vr_song_0_dict.keys()
    # ), "Engine and VDJ have different keys"

    for index, rb_song in enumerate(rb_tracks):
        en_song = en_tracks[index]
        se_song = se_tracks[index]
        tr_song = tr_tracks[index]
        vr_song = vr_tracks[index]

        assert (
            rb_song.artist == en_song.artist == se_song.artist == tr_song.artist == vr_song.artist
        )
        assert rb_song.title == en_song.title == se_song.title == tr_song.title == vr_song.title
        assert rb_song.year == en_song.year == se_song.year == tr_song.year == vr_song.year
        assert approx(rb_song.duration, abs=1) == en_song.duration
        assert approx(rb_song.duration, abs=1) == tr_song.duration
        assert approx(rb_song.duration, abs=1) == vr_song.duration
