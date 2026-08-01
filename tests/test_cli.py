import json

from playlistparser.cli import main


def test_parse_prints_numbered_tracks_and_summary(capsys):
    assert main(["parse", "data/rekordbox_1.txt"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "1. E-Type - When I Close My Eyes (Feat NaN"
    assert lines[-2] == ""
    assert lines[-1] == "Rekordbox · 16 tracks"


def test_parse_json_output(capsys):
    assert main(["parse", "data/enginedj-v21.csv", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"] == {"playlist_type": "ENGINE", "track_count": 4}
    assert payload["tracks"][0]["artist"] == "Aikakone"
    assert payload["tracks"][0]["bpm"] == 130.0


def test_parse_unknown_format_fails(capsys):
    assert main(["parse", "data/brokentestfile.dat"]) == 1
    assert "error:" in capsys.readouterr().err


def test_parse_missing_file_fails(capsys):
    assert main(["parse", "data/nope.csv"]) == 1
    assert "error:" in capsys.readouterr().err
