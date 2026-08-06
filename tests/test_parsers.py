import csv
from pathlib import Path

import pytest

from playlistparser import FieldName, MalformedPlaylistError, MissingFieldError, PlaylistParser

DATA = Path(__file__).resolve().parent.parent / "data"

ENGINE_FILE = DATA / "enginedj-v21.csv"
REKORDBOX_FILE = DATA / "rekordbox-v6.txt"
SERATO_FILE = DATA / "serato-v25.csv"
TRAKTOR_FILE = DATA / "traktor-v35.nml"
VIRTUALDJ_FILE = DATA / "virtualdj-v2021.csv"


@pytest.mark.parametrize(
    ("title", "artist", "track_path", "expected_artist", "expected_title"),
    [
        (
            "History Artist - Track - Club Mix",
            "",
            "/music/track.mp3.temp#history#event.temp",
            "History Artist",
            "Track - Club Mix",
        ),
        (
            "Title containing - a separator",
            "Tagged Artist",
            "/music/track.mp3.temp#history#event.temp",
            "Tagged Artist",
            "Title containing - a separator",
        ),
        (
            "Title containing - a separator",
            "",
            "/music/track.mp3",
            "Fallback Artist",
            "Title containing - a separator",
        ),
        (
            "Unsplittable title",
            "",
            "/music/track.mp3.temp#history#event.temp",
            "Fallback Artist",
            "Unsplittable title",
        ),
    ],
)
def test_engine_history_metadata_resolution(
    tmp_path: Path,
    title: str,
    artist: str,
    track_path: str,
    expected_artist: str,
    expected_title: str,
) -> None:
    playlist = tmp_path / "history.csv"
    with playlist.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["#", "Title", "Artist", "Length", "BPM", "Year", "File name"])
        writer.writerow([1, title, artist, 60, 120, 2026, track_path])

    track = PlaylistParser(playlist, default_artist="Fallback Artist").to_list()[0]

    assert (track.artist, track.title) == (expected_artist, expected_title)


@pytest.mark.parametrize(
    (
        "file_path",
        "track_index",
        "expected_album",
        "expected_key",
        "expected_bpm",
        "expected_path",
        "expected_vendor_state",
    ),
    [
        (
            ENGINE_FILE,
            0,
            "Greatest Hits",
            "",
            130.0,
            "/Volumes/Sammy/iTunes/iTunes Music/Music/Aikakone/Greatest Hits/2-05 Tähtikaaren Taa (2008 Remix).mp3",
            "empty",
        ),
        (
            REKORDBOX_FILE,
            3,
            "1998 (Single)",
            "Bm",
            137.5,
            "/Volumes/Sammy/iTunes/iTunes Music/Music/Binary Finary/1998 (Single)/02 1998 (Paul Van Dyk Remix).mp3",
            "empty",
        ),
        (SERATO_FILE, 0, "", "", 0.0, "", "empty"),
        (
            TRAKTOR_FILE,
            3,
            "1998 (Single)",
            "Bm",
            137.7,
            "/Users/uninen/Documents/02 1998 (Paul Van Dyk Remix).mp3",
            "present",
        ),
        (VIRTUALDJ_FILE, 2, "", "F", 137.9, "", "empty"),
    ],
)
def test_source_metadata(
    file_path: Path,
    track_index: int,
    expected_album: str,
    expected_key: str,
    expected_bpm: float,
    expected_path: str,
    expected_vendor_state: str,
) -> None:
    track = PlaylistParser(file_path).to_list()[track_index]

    assert track.album == expected_album
    assert track.key == expected_key
    assert track.bpm == expected_bpm
    assert track.file_path == expected_path
    vendor_state = "present" if track.vendor_id else "empty"
    assert vendor_state == expected_vendor_state


@pytest.mark.parametrize(
    ("file_path", "required_field"),
    [
        (DATA / "rekordbox-v6-missing-meta.txt", "title"),
        (DATA / "rekordbox-v6-missing-meta.txt", "duration"),
        (DATA / "rekordbox-v6-missing-meta.txt", "bpm"),
        (DATA / "PlaylistConverterTest-wo-year.txt", "year"),
        (DATA / "rekordbox_1.txt", "file_path"),
        (SERATO_FILE, "duration"),
        (SERATO_FILE, "bpm"),
        (SERATO_FILE, "file_path"),
        (VIRTUALDJ_FILE, "file_path"),
        (ENGINE_FILE, "artist"),
        (REKORDBOX_FILE, "artist"),
        (SERATO_FILE, "artist"),
        (TRAKTOR_FILE, "artist"),
        (VIRTUALDJ_FILE, "artist"),
    ],
)
def test_required_field(file_path: Path, required_field: FieldName) -> None:
    with pytest.raises(MissingFieldError) as error_info:
        PlaylistParser(file_path, require=[required_field]).to_list()

    assert error_info.value.field == required_field


def test_traktor_yields_playlist_order() -> None:
    """NML COLLECTION is an unordered database; the PLAYLIST node carries the set order."""
    titles = [track.title for track in PlaylistParser(DATA / "traktor_3.nml")]

    assert titles == [
        "Music Takes You Higher (Radio Mix)",
        "Wrap Me Up (Dancing Divaz Edit)",
        "Inferno (Fired Up Mix)",
        "Twilight Zone",
        "Do You See The Light",
        "Fuk U In The Ass (Pegasus Radio Mix)",
        "Time is Up (FM Edit)",
    ]


@pytest.mark.parametrize(
    ("file_path", "expected_count"),
    [
        (DATA / "traktor_1.nml", 16),
        (DATA / "traktor_2.nml", 26),
        (DATA / "traktor_3.nml", 7),
        (TRAKTOR_FILE, 4),
    ],
)
def test_traktor_loses_no_tracks(file_path: Path, expected_count: int) -> None:
    titles = [track.title for track in PlaylistParser(file_path)]

    assert len(titles) == expected_count
    assert len(set(titles)) == expected_count
    assert all(titles)


def test_traktor_without_playlist_node_falls_back_to_collection_order() -> None:
    titles = [track.title for track in PlaylistParser(DATA / "traktor-missing-playtime.nml")]

    assert titles == ["Track With No Playtime", "Track With Playtime"]


def test_traktor_progress_total_counts_playlist_not_collection(tmp_path: Path) -> None:
    """A collection can dwarf the playlist; progress must report the playlist size."""
    entries = "".join(
        f'<ENTRY TITLE="Track {n}" ARTIST="Artist {n}">'
        f'<LOCATION DIR="/:music/:" FILE="{n}.mp3" VOLUME="Disk"></LOCATION></ENTRY>'
        for n in range(5)
    )
    references = "".join(f'<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="Disk/:music/:{n}.mp3"/></ENTRY>' for n in (3, 1))
    playlist = tmp_path / "big-collection.nml"
    playlist.write_text(
        f'<?xml version="1.0"?><NML VERSION="19"><COLLECTION ENTRIES="5">{entries}</COLLECTION>'
        f'<PLAYLISTS><NODE TYPE="PLAYLIST"><PLAYLIST ENTRIES="2" TYPE="LIST">{references}</PLAYLIST>'
        f"</NODE></PLAYLISTS></NML>",
    )

    totals: list[int | None] = []
    tracks = list(PlaylistParser(playlist).stream(on_progress=lambda done, total, *_: totals.append(total)))

    assert [track.title for track in tracks] == ["Track 3", "Track 1"]
    assert set(totals) == {2}


def nml_entry(title: str, filename: str, *, album: str | None = "An Album") -> str:
    """One COLLECTION ENTRY; album=None omits the ALBUM node entirely."""
    album_node = f'<ALBUM TITLE="{album}"></ALBUM>' if album is not None else ""
    return (
        f'<ENTRY TITLE="{title}" ARTIST="Artist of {title}">{album_node}'
        f'<LOCATION DIR="/:music/:" FILE="{filename}" VOLUME="Disk"></LOCATION></ENTRY>'
    )


def write_nml(path: Path, entries: list[str], playlists: list[list[str]] | None) -> Path:
    """Write an NML file; playlists=None omits the PLAYLISTS section."""
    collection = f'<COLLECTION ENTRIES="{len(entries)}">{"".join(entries)}</COLLECTION>'
    nodes = "".join(
        f'<NODE TYPE="PLAYLIST"><PLAYLIST ENTRIES="{len(filenames)}" TYPE="LIST">'
        + "".join(f'<ENTRY><PRIMARYKEY TYPE="TRACK" KEY="Disk/:music/:{name}"/></ENTRY>' for name in filenames)
        + "</PLAYLIST></NODE>"
        for filenames in playlists or []
    )
    body = collection if playlists is None else f"{collection}<PLAYLISTS>{nodes}</PLAYLISTS>"
    path.write_text(f'<?xml version="1.0"?><NML VERSION="19">{body}</NML>')
    return path


def test_traktor_empty_playlist_yields_no_tracks(tmp_path: Path) -> None:
    """An empty PLAYLIST selects nothing; the collection behind it is not the playlist."""
    playlist = write_nml(
        tmp_path / "empty-playlist.nml",
        [nml_entry(f"Track {n}", f"{n}.mp3") for n in range(3)],
        [[]],
    )

    assert PlaylistParser(playlist).to_list() == []


def test_traktor_require_ignores_collection_tracks_outside_playlist(tmp_path: Path) -> None:
    """An incomplete library track must not abort a playlist that never references it."""
    playlist = write_nml(
        tmp_path / "unreferenced-incomplete.nml",
        [
            nml_entry("Complete A", "a.mp3"),
            nml_entry("No Album", "b.mp3", album=None),
            nml_entry("Complete C", "c.mp3"),
        ],
        [["c.mp3", "a.mp3"]],
    )

    titles = [track.title for track in PlaylistParser(playlist, require=["album"])]

    assert titles == ["Complete C", "Complete A"]


def test_traktor_require_raises_for_referenced_incomplete_track(tmp_path: Path) -> None:
    playlist = write_nml(
        tmp_path / "referenced-incomplete.nml",
        [nml_entry("Complete A", "a.mp3"), nml_entry("No Album", "b.mp3", album=None)],
        [["a.mp3", "b.mp3"]],
    )

    with pytest.raises(MissingFieldError) as error_info:
        PlaylistParser(playlist, require=["album"]).to_list()

    assert error_info.value.field == "album"
    assert error_info.value.track_title == "No Album"


def test_traktor_require_raises_without_playlist_node(tmp_path: Path) -> None:
    """Without a PLAYLIST the whole collection is yielded, so all of it must satisfy require."""
    playlist = write_nml(
        tmp_path / "collection-only-incomplete.nml",
        [nml_entry("Complete A", "a.mp3"), nml_entry("No Album", "b.mp3", album=None)],
        None,
    )

    with pytest.raises(MissingFieldError) as error_info:
        PlaylistParser(playlist, require=["album"]).to_list()

    assert error_info.value.field == "album"


def test_truncated_nml_raises_malformed_playlist_error(tmp_path: Path) -> None:
    playlist = tmp_path / "truncated.nml"
    playlist.write_text('<?xml version="1.0"?><NML><COLLECTION ENTRIES="1"><ENTRY TITLE="Cut Off"')

    with pytest.raises(MalformedPlaylistError) as error_info:
        PlaylistParser(playlist).to_list()

    assert error_info.value.path == playlist
    assert error_info.value.line == 1
