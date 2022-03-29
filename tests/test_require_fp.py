from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser

ROOT_DIR = Path(__file__).resolve().parent.parent

ENGINE_FILE = join(ROOT_DIR, "data/enginedj-v21.csv")
REKORDBOX_FILE = join(ROOT_DIR, "data/rekordbox-v6.txt")
SERATO_FILE = join(ROOT_DIR, "data/serato-v25.csv")
TRAKTOR_FILE = join(ROOT_DIR, "data/traktor-v35.nml")
VIRTUALDJ_FILE = join(ROOT_DIR, "data/virtualdj-v2021.csv")

verbose = False


def test_not_implemented():
    with pytest.raises(NotImplementedError):
        PlaylistParser(SERATO_FILE, require_fp=True, verbose=verbose)

    with pytest.raises(NotImplementedError):
        PlaylistParser(TRAKTOR_FILE, require_fp=True, verbose=verbose)

    with pytest.raises(NotImplementedError):
        PlaylistParser(VIRTUALDJ_FILE, require_fp=True, verbose=verbose)
