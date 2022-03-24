from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser
from playlistparser.utils import time_str_to_seconds

ROOT_DIR = Path(__file__).resolve().parent.parent

BROKEN_FILE = join(ROOT_DIR, "data/brokentestfile.dat")
FIVE_ARTISTS = join(ROOT_DIR, "data/TestList5Artists.txt")
HUNDRED_TRACKS = join(ROOT_DIR, "data/TestList100tracks.txt")

verbose = False


def test_broken_file():
    with pytest.raises(Exception) as exc_info:
        PlaylistParser(BROKEN_FILE, verbose=verbose)
    assert str(exc_info.value).startswith("Unknown playlist type when opening")


def test_utils():
    assert time_str_to_seconds("00:00:00") == 0
    assert time_str_to_seconds("00:00:10") == 10
    assert time_str_to_seconds("00:01:00") == 60
    assert time_str_to_seconds("00:10:00") == 600
    assert time_str_to_seconds("01:00:00") == 3600
    assert time_str_to_seconds("foo") == 0


def test_num_artists():
    parser = PlaylistParser(FIVE_ARTISTS, verbose=verbose)
    tracks = parser.get_tracks()
    assert len(tracks) == 100
    artists = set()
    for track in tracks:
        artists.add(track.artist)
    assert len(artists) == 5


def test_num_tracks():
    parser = PlaylistParser(HUNDRED_TRACKS, verbose=verbose)
    tracks = parser.get_tracks()
    assert len(tracks) == 100
    artists = set()
    for track in tracks:
        artists.add(track.artist)
    assert len(artists) == 81
