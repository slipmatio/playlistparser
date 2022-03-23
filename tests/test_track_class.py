from playlistparser.track import Track

verbose = False


def test_track_class():
    track = Track(title="test title", artist="test artist", year="2022", duration=10)
    assert track.title == "test title"
    assert track.year == 2022
    assert track.duration_str() == "0:10"
    assert str(track) == "test artist - test title"

    track = Track(title="test", artist="test", year="2022", duration=0)
    assert track.duration_str() == "0:00"

    track = Track(title="test", artist="test", year="2022-1-1", duration=60)
    assert track.duration_str() == "1:00"
    assert track.year == 2022

    track = Track(title="test", artist="test", year="2022/1/1", duration=360)
    assert track.duration_str() == "6:00"
    assert track.year == 2022

    track = Track(title="test", artist="test", year="2022/1/1", duration=3600)
    assert track.duration_str() == "1:00:00"

    track = Track(
        title="test",
        artist="test",
        year="2022/1/1",
        duration=2 * 3600 + 45 * 60 + 15,
        bpm=100,
    )
    assert track.duration_str() == "2:45:15"
    assert len(track.as_dict().keys()) == 6
    assert len(track.as_dict(no_meta=True).keys()) == 2
