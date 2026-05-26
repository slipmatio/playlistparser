"""Per-format integration tests and require= / MissingFieldError coverage."""

from pathlib import Path

import pytest

import playlistparser as pp
from playlistparser import MissingFieldError

DATA = Path(__file__).resolve().parent.parent / "data"

ENGINE_FILE = DATA / "enginedj-v21.csv"
REKORDBOX_FILE = DATA / "rekordbox-v6.txt"
RB_MISSING_META_FILE = DATA / "rekordbox-v6-missing-meta.txt"
REKORDBOX_NOPATHS_FILE = DATA / "rekordbox_1.txt"
SERATO_FILE = DATA / "serato-v25.csv"
TRAKTOR_FILE = DATA / "traktor-v35.nml"
TRAKTOR_MISSING_PLAYTIME = DATA / "traktor-missing-playtime.nml"
VIRTUALDJ_FILE = DATA / "virtualdj-v2021.csv"
RB_WO_YEAR = DATA / "PlaylistConverterTest-wo-year.txt"
RB_W_YEAR = DATA / "PlaylistConverterTest.txt"


# Engine DJ


def test_engine_basic():
    tracks = pp.parse(ENGINE_FILE)
    assert len(tracks) == 4
    assert tracks[0].year > 0
    assert tracks[0].duration > 0
    assert tracks[0].bpm > 0
    assert tracks[0].file_path != ""
    assert tracks[2].artist == "Unknown Artist"


def test_engine_require_fp():
    # Engine supports file_path — requiring it on a file that has paths works.
    tracks = pp.parse(ENGINE_FILE, require=["file_path"])
    assert len(tracks) == 4
    assert all(t.file_path for t in tracks)


# Rekordbox


def test_rekordbox_basic():
    tracks = pp.parse(REKORDBOX_FILE)
    assert len(tracks) == 4
    assert tracks[0].year > 0
    assert tracks[0].duration > 0
    assert tracks[2].artist == "Unknown Artist"


def test_rekordbox_require_title_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(RB_MISSING_META_FILE, require=["title"])
    err = exc_info.value
    assert err.field == "title"
    assert err.line is not None


def test_rekordbox_require_duration_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(RB_MISSING_META_FILE, require=["duration"])
    assert exc_info.value.field == "duration"


def test_rekordbox_require_bpm_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(RB_MISSING_META_FILE, require=["bpm"])
    assert exc_info.value.field == "bpm"


def test_rekordbox_require_year_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(RB_MISSING_META_FILE, require=["year"])
    assert exc_info.value.field == "year"

    with pytest.raises(MissingFieldError):
        pp.parse(RB_WO_YEAR, require=["year"])

    tracks = pp.parse(RB_W_YEAR, require=["year"])
    assert len(tracks) == 4


def test_rekordbox_require_fp_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(REKORDBOX_NOPATHS_FILE, require=["file_path"])
    assert exc_info.value.field == "file_path"


def test_rekordbox_no_paths_ok():
    tracks = pp.parse(REKORDBOX_NOPATHS_FILE)
    assert len(tracks) == 16


def test_rekordbox_missing_meta_no_require():
    # Without require= the file should parse (yielding 4 tracks with empty fields).
    tracks = pp.parse(RB_MISSING_META_FILE)
    assert len(tracks) == 4


# Serato


def test_serato_basic():
    tracks = pp.parse(SERATO_FILE)
    assert len(tracks) == 4
    assert tracks[0].year > 0
    assert tracks[2].artist == "Unknown Artist"


def test_serato_as_dict_keys():
    tracks = pp.parse(SERATO_FILE)
    # Serato only exposes title, artist, year
    d = tracks[0].as_dict()
    assert "year" in d
    assert "duration" not in d
    assert "bpm" not in d


def test_serato_require_title_missing(tmp_path):
    path = tmp_path / "serato-missing-title.csv"
    path.write_text(
        '"name","artist","year"\n"session","",""\n"","Artist","2008"\n',
        encoding="utf-8",
    )

    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(path, require=["title"])
    assert exc_info.value.field == "title"


def test_serato_require_year_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(SERATO_FILE, require=["year"])
    assert exc_info.value.field == "year"


# Traktor


def test_traktor_basic():
    tracks = pp.parse(TRAKTOR_FILE)
    assert len(tracks) == 4
    assert tracks[0].year > 0
    assert tracks[0].duration > 0
    assert tracks[2].artist == "Unknown Artist"


def test_traktor_missing_playtime_defaults_to_zero():
    tracks = pp.parse(TRAKTOR_MISSING_PLAYTIME)
    assert len(tracks) == 2
    assert tracks[0].duration == 0
    assert tracks[1].duration == 243


def test_traktor_require_duration_raises_when_playtime_missing():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(TRAKTOR_MISSING_PLAYTIME, require=["duration"])
    assert exc_info.value.field == "duration"


@pytest.mark.parametrize(
    ("file_path", "required_field"),
    [
        (SERATO_FILE, "duration"),
        (SERATO_FILE, "bpm"),
        (SERATO_FILE, "file_path"),
        (TRAKTOR_FILE, "file_path"),
        (VIRTUALDJ_FILE, "file_path"),
    ],
)
def test_require_unsupported_field_raises(file_path, required_field):
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(file_path, require=[required_field])
    assert exc_info.value.field == required_field


# VirtualDJ


def test_virtualdj_basic():
    tracks = pp.parse(VIRTUALDJ_FILE)
    assert len(tracks) == 4
    assert tracks[0].year > 0
    assert tracks[0].duration > 0
    assert tracks[2].artist == "Unknown Artist"


def test_virtualdj_require_year():
    with pytest.raises(MissingFieldError) as exc_info:
        # The "Orkidea" track has empty year; use bpm requirement to trigger on it
        # Actually the track with empty year also has a duration, so require year:
        pp.parse(VIRTUALDJ_FILE, require=["year"])
    assert exc_info.value.field == "year"


def test_virtualdj_require_bpm():
    with pytest.raises(MissingFieldError) as exc_info:
        pp.parse(DATA / "virtualdj-missing-bpm.csv", require=["bpm"])
    assert exc_info.value.field == "bpm"


def test_duration_consistency():
    rb = pp.parse(REKORDBOX_FILE)
    en = pp.parse(ENGINE_FILE)
    tr = pp.parse(TRAKTOR_FILE)
    vj = pp.parse(VIRTUALDJ_FILE)

    for i in range(len(rb)):
        assert pytest.approx(rb[i].duration, abs=1) == en[i].duration
        assert pytest.approx(rb[i].duration, abs=1) == tr[i].duration
        assert pytest.approx(rb[i].duration, abs=1) == vj[i].duration
