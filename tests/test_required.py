from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser

ROOT_DIR = Path(__file__).resolve().parent.parent

ENGINE_FILE = join(ROOT_DIR, "data/enginedj-v21.csv")
REKORDBOX_FILE = join(ROOT_DIR, "data/rekordbox-v6.txt")
REKORDBOX_NOPATHS_FILE = join(ROOT_DIR, "data/rekordbox_1.txt")
SERATO_FILE = join(ROOT_DIR, "data/serato-v25.csv")
TRAKTOR_FILE = join(ROOT_DIR, "data/traktor-v35.nml")
VIRTUALDJ_FILE = join(ROOT_DIR, "data/virtualdj-v2021.csv")

verbose = False


def test_not_implemented():
    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(SERATO_FILE, require_fp=True, verbose=verbose)
        parser.parse()

    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(TRAKTOR_FILE, require_fp=True, verbose=verbose)
        parser.parse()

    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(VIRTUALDJ_FILE, require_fp=True, verbose=verbose)
        parser.parse()


def test_rekordbox():
    with pytest.raises(ValueError):
        parser = PlaylistParser(REKORDBOX_NOPATHS_FILE, require_fp=True, verbose=verbose)
        parser.parse()

    parser = PlaylistParser(REKORDBOX_NOPATHS_FILE, require_fp=False, verbose=verbose)
    parser.parse()
    assert len(parser.tracks) == 16


def test_engine():
    parser = PlaylistParser(ENGINE_FILE, require_fp=True, verbose=verbose)
    parser.parse()
    assert len(parser.tracks) == 4

    parser = PlaylistParser(ENGINE_FILE, require_fp=False, verbose=verbose)
    parser.parse()
    assert len(parser.tracks) == 4
