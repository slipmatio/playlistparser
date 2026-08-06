# Playlistparser

Tool for parsing DJ software playlists. Currently supports Engine DJ, Rekordbox, Serato, Traktor,
and VirtualDJ. Part of [Slipmat.io](https://slipmat.io) music tools.

Free hosted version of this tool:
[https://slipmat.io/tools/playlistconverter/](https://slipmat.io/tools/playlistconverter/)

## Installing

`uv add playlistparser`

## Command line

```bash
uvx playlistparser parse myplaylist.nml
```

```text
1. Technotronic - Pump Up The Jam (Edit)
2. Guru Josh - Infinity (1990s... Time for the Guru 12" Mix)

Rekordbox · 2 tracks
```

`--json` gives every field of every track:

```json
{
  "tracks": [
    {
      "title": "Pump Up The Jam (Edit)",
      "artist": "Technotronic",
      "album": "",
      "key": "",
      "duration": 216,
      "year": 1989,
      "bpm": 124.0,
      "file_path": "",
      "vendor_id": ""
    }
  ],
  "summary": { "playlist_type": "REKORDBOX", "track_count": 1 }
}
```

Exit code is 1 if the file can't be parsed.

## Usage

```python
import logging

from playlistparser import (
    MalformedPlaylistError,
    MissingFieldError,
    PlaylistParser,
    PlaylistParserError,
    PlaylistType,
    UnknownFormatError,
)

logging.basicConfig(level=logging.INFO)

try:
    # Every keyword argument is optional.
    #
    #   require        — raise MissingFieldError when a listed field is missing from a
    #                    row. Fields the format cannot expose at all (Serato has no bpm)
    #                    raise before parsing starts; CSV detection reads the header first.
    #   as_type        — bypass detection, which otherwise uses the file extension and,
    #                    for .csv, the header row.
    #   default_artist — substituted for a missing artist, unless "artist" is in require.
    #
    # Recoverable per-row warnings go to the `playlistparser.parsers.*` stdlib loggers
    # (route through structlog with `structlog.stdlib.LoggerFactory()`).
    pl = PlaylistParser(
        "history.csv",
        require=["title", "artist"],
        default_artist="Unknown Artist",
        # as_type=PlaylistType.ENGINE,
    )

    # ENGINE, REKORDBOX, SERATO, TRAKTOR or VIRTUALDJ. For .csv, a one-time header sniff.
    print(f"Format: {pl.playlist_type.name}")

    # Lazy — every pass re-reads the file.
    for track in pl:
        print(track)  # "Artist - Title"

        # Frozen dataclass; every field is always present, missing values are 0 or "".
        #   title, artist, album, key, file_path, vendor_id: str
        #   duration: int (seconds), year: int, bpm: float
        print(track.bpm, track.year, track.duration_str())  # "128.0 2024 6:42"

        payload = track.as_dict()  # no_meta=True keeps only title and artist

    # Materialise once; cached for the parser's lifetime.
    print(f"{pl.track_count} tracks, {pl.total_duration}s total")
    tracks = pl.to_list()

except UnknownFormatError as e:
    # Extension unrecognised, or a CSV header matching no known format. Override with as_type.
    print(f"Unsupported file: {e}")

except MissingFieldError as e:
    print(f"Missing '{e.field}' on line {e.line}: {e.track_title!r}")

except MalformedPlaylistError as e:
    # Bad XML, truncated row. e.path and e.line locate it.
    print(f"Corrupt playlist: {e}")

except PlaylistParserError as e:
    # Base class for all of the above.
    print(f"Could not parse playlist: {e}")

except FileNotFoundError:
    # Nothing is opened until the first iteration or aggregate access.
    print("Playlist file does not exist")
```

### Parsing progress

Pass a callback to `stream()`:

```python
def report_progress(tracks_done, total_tracks, bytes_read, bytes_total):
    byte_percent = bytes_read / bytes_total if bytes_total else 1
    print(tracks_done, total_tracks, byte_percent)


for track in PlaylistParser("set.nml").stream(on_progress=report_progress):
    save(track)
```

Byte progress is monotonic and completes even when malformed source records are skipped. Track
totals count source records, so `tracks_done` can finish below `total_tracks`. Traktor totals come
from the `PLAYLIST` entry counts, falling back to `COLLECTION` for files with no playlist node;
delimited formats count logical records in a pre-pass. `total_tracks` is `None` when the source
exposes no valid count.

### Supported formats and fields

| Format    | `PlaylistType` | Extension |
| --------- | -------------- | --------- |
| Engine DJ | `ENGINE`       | `.csv`    |
| Rekordbox | `REKORDBOX`    | `.txt`    |
| Serato    | `SERATO`       | `.csv`    |
| Traktor   | `TRAKTOR`      | `.nml`    |
| VirtualDJ | `VIRTUALDJ`    | `.csv`    |

CSV formats are detected by sniffing the header row.

Tracks are yielded in playlist order. For Traktor that is the `PLAYLIST` node's `PRIMARYKEY` order,
not the unordered `COLLECTION`; an `.nml` with no `PLAYLIST` node falls back to collection order.

BPM is a float rounded to one decimal place. Traktor's `vendor_id` is its `ENTRY.AUDIO_ID`.

| Format    | title | artist | album | key | duration | year | bpm | file_path | vendor_id |
| --------- | :---: | :----: | :---: | :-: | :------: | :--: | :-: | :-------: | :-------: |
| Engine DJ |   x   |   x    |   x   |     |    x     |  x   |  x  |     x     |           |
| Rekordbox |   x   |   x    |   x   |  x  |    x     |  x   |  x  |     x     |           |
| Serato    |   x   |   x    |       |     |          |  x   |     |           |           |
| Traktor   |   x   |   x    |   x   |  x  |    x     |  x   |  x  |     x     |     x     |
| VirtualDJ |   x   |   x    |       |  x  |    x     |  x   |  x  |           |           |

## Developing

- `uv run ruff format` - format
- `uv run ruff check --fix --extend-fixable F401` - lint
- `uv run ty check` - typecheck
- `uv run pytest` - run test suite

## Contributing

Contributions are welcome! Please follow the [code of conduct](./CODE_OF_CONDUCT.md) when
interacting with others.

## Elsewhere

- [Follow @uninen.net](https://bsky.app/profile/uninen.net) on Bluesky
- Read my continuously updating learnings from Python / TypeScript and other Web development topics
  from my [Today I Learned site](https://til.unessa.net/)

## Licence

Copyright © 2022, Ville Säävuori. Released under the GNU Affero General Public License v3.0.

Commercial licenses are also available.
