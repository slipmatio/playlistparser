from os.path import join
from pathlib import Path

import pytest
from playlistparser import PlaylistParser

ROOT_DIR = Path(__file__).resolve().parent.parent

ENGINE_FILE = join(ROOT_DIR, "data/enginedj-v21.csv")
REKORDBOX_FILE = join(ROOT_DIR, "data/rekordbox-v6.txt")
RB_MISSING_META_FILE = join(ROOT_DIR, "data/rekordbox-v6-missing-meta.txt")
REKORDBOX_NOPATHS_FILE = join(ROOT_DIR, "data/rekordbox_1.txt")
SERATO_FILE = join(ROOT_DIR, "data/serato-v25.csv")
TRAKTOR_FILE = join(ROOT_DIR, "data/traktor-v35.nml")
VIRTUALDJ_FILE = join(ROOT_DIR, "data/virtualdj-v2021.csv")
REKORDBOX_TEST_WO_YEAR = join(ROOT_DIR, "data/PlaylistConverterTest-wo-year.txt")
REKORDBOX_TEST_W_YEAR = join(ROOT_DIR, "data/PlaylistConverterTest.txt")

verbose = False


def test_serato_not_implemented():
    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(SERATO_FILE, require_fp=True, verbose=verbose)
        parser.parse()

    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(SERATO_FILE, require_bpm=True, verbose=verbose)
        parser.parse()

    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(SERATO_FILE, require_year=True, verbose=verbose)
        parser.parse()


def test_traktor_not_implemented():
    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(TRAKTOR_FILE, require_fp=True, verbose=verbose)
        parser.parse()


def test_virtualdj_not_implemented():
    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(VIRTUALDJ_FILE, require_fp=True, verbose=verbose)
        parser.parse()

    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(VIRTUALDJ_FILE, require_bpm=True, verbose=verbose)
        parser.parse()

    with pytest.raises(NotImplementedError):
        parser = PlaylistParser(VIRTUALDJ_FILE, require_year=True, verbose=verbose)
        parser.parse()


def test_rekordbox_title():

    # Test require_title
    parser = PlaylistParser(REKORDBOX_NOPATHS_FILE, require_title=True, verbose=verbose)
    parser.parse()
    assert len(parser.tracks) == 16

    with pytest.raises(ValueError):
        parser = PlaylistParser(RB_MISSING_META_FILE, require_title=True, verbose=verbose)
        parser.parse()


def test_rekordbox_duration():
    with pytest.raises(ValueError):
        parser = PlaylistParser(
            RB_MISSING_META_FILE, require_title=False, require_duration=True, verbose=verbose
        )
        parser.parse()

    parser = PlaylistParser(
        REKORDBOX_NOPATHS_FILE, require_title=False, require_duration=True, verbose=verbose
    )
    parser.parse()
    assert len(parser.tracks) == 16


def test_rekordbox_bpm():
    with pytest.raises(ValueError):
        parser = PlaylistParser(
            RB_MISSING_META_FILE, require_title=False, require_bpm=True, verbose=verbose
        )
        parser.parse()

    parser = PlaylistParser(
        REKORDBOX_NOPATHS_FILE, require_title=False, require_bpm=True, verbose=verbose
    )
    parser.parse()
    assert len(parser.tracks) == 16


def test_rekordbox_year():
    parser = PlaylistParser(
        RB_MISSING_META_FILE, require_title=False, require_year=False, verbose=verbose
    )
    parser.parse()
    assert len(parser.tracks) == 4

    with pytest.raises(ValueError):
        parser = PlaylistParser(
            RB_MISSING_META_FILE, require_title=False, require_year=True, verbose=verbose
        )
        parser.parse()

    with pytest.raises(ValueError):
        parser = PlaylistParser(REKORDBOX_TEST_WO_YEAR, require_year=True, verbose=verbose)
        parser.parse()

    parser2 = PlaylistParser(REKORDBOX_TEST_W_YEAR, require_year=True, verbose=verbose)
    parser2.parse()
    assert len(parser2.tracks) == 4


def test_rekordbox_fp():

    # Test require_fp
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
