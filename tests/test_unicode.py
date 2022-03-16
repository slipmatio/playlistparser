from playlistparser.track import Track


def test_unicode_normalization():
    # b'e\xcc\x81'
    track1 = Track(title="test é", artist="artist", year="2022", duration=10)
    # b'\xc3\xa9'
    track2 = Track(title="test é", artist="artist", year="2022", duration=10)

    assert track1.title == track2.title

    # b'e\xcc\x81'
    track3 = Track(title="test", artist="artist é", year="2022", duration=10)
    # b'\xc3\xa9'
    track4 = Track(title="test", artist="artist é", year="2022", duration=10)

    assert track3.artist == track4.artist


def test_unicode():

    track5 = Track(title="test", artist="ロビンソン", year="2022", duration=10)
    assert track5.artist == "ロビンソン"

    track6 = Track(title="СКАЙ", artist="artist", year="2022", duration=10)
    assert track6.title == "СКАЙ"

    track7 = Track(title="ääööÅÅ", artist="artist", year="2022", duration=10)
    assert track7.title == "ääööÅÅ"
