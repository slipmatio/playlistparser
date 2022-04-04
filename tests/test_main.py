from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser, PlaylistType
from playlistparser.utils import time_str_to_seconds

ROOT_DIR = Path(__file__).resolve().parent.parent

BROKEN_FILE = join(ROOT_DIR, "data/brokentestfile.dat")
FIVE_ARTISTS = join(ROOT_DIR, "data/TestList5Artists.txt")
HUNDRED_TRACKS = join(ROOT_DIR, "data/TestList100tracks.txt")

ENGINE_FILE = join(ROOT_DIR, "data/enginedj-v21.csv")
REKORDBOX_FILE = join(ROOT_DIR, "data/rekordbox-v6.txt")
SERATO_FILE = join(ROOT_DIR, "data/serato-v25.csv")
TRAKTOR_FILE = join(ROOT_DIR, "data/traktor-v35.nml")
VIRTUALDJ_FILE = join(ROOT_DIR, "data/virtualdj-v2021.csv")

verbose = False


def test_broken_file():
    with pytest.raises(Exception) as exc_info:
        PlaylistParser(BROKEN_FILE, verbose=verbose)
    assert str(exc_info.value).startswith("Couldn't determine playlist type")


def test_utils():
    assert time_str_to_seconds("00:00:00") == 0
    assert time_str_to_seconds("00:00:10") == 10
    assert time_str_to_seconds("00:01:00") == 60
    assert time_str_to_seconds("00:10:00") == 600
    assert time_str_to_seconds("01:00:00") == 3600
    assert time_str_to_seconds("foo") == 0


def test_num_artists():
    parser = PlaylistParser(FIVE_ARTISTS, verbose=verbose)
    parser.parse()
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


def test_playlist_type():
    parser = PlaylistParser(HUNDRED_TRACKS, verbose=verbose)
    assert parser.playlist_type == PlaylistType.REKORDBOX
    assert int(parser.playlist_type) == 2


@pytest.mark.parametrize(
    "file_name",
    [
        ENGINE_FILE,
        REKORDBOX_FILE,
        SERATO_FILE,
        TRAKTOR_FILE,
        VIRTUALDJ_FILE,
    ],
)
def test_default_artist(file_name):
    parser = PlaylistParser(file_name, verbose=verbose)
    tracks = parser.get_tracks()
    assert tracks[2].artist == "Unknown Artist"

    parser = PlaylistParser(file_name, default_artist="Default", verbose=verbose)
    tracks = parser.get_tracks()
    assert tracks[2].artist == "Default"
