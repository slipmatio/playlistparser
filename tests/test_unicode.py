from playlistparser.track import Track


def test_unicode_normalization():
    # b'e\xcc\x81'
    track1 = Track(title="test é", artist="artist", year="2022", duration=10)
    # b'\xc3\xa9'
    track2 = Track(title="test é", artist="artist", year="2022", duration=10)

    assert track1.title == track2.title
