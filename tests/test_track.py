from src.playlistparser.track import Track


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
