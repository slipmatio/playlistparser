# Playlistparser

Tool for parsing DJ software playlists. Currently supports Engine DJ, Rekordbox, Serato, Traktor,
and VirtualDJ. Part of [Slipmat.io](https://slipmat.io) tools.

Free hosted version of this tool:
[https://slipmat.io/tools/playlist-converter/](https://slipmat.io/tools/playlist-converter/)

## Installing

`uv add playlistparser`

## Usage

One end-to-end example covering format detection, streaming, required fields,
aggregates, per-track data and every exception you need to handle:

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
    # Construct a parser. All keyword arguments are optional.
    #
    #   require        — fail fast if any listed field is missing on a row.
    #                    If the format itself can't expose the field (e.g. Serato
    #                    has no bpm), MissingFieldError is raised immediately,
    #                    before any I/O.
    #   as_type        — override format detection (use for unusual file
    #                    extensions); otherwise the format is detected from the
    #                    extension, and for .csv from the header row.
    #   default_artist — substituted when a row has no artist field.
    #
    # Recoverable per-row warnings are emitted via stdlib `logging` under the
    # `playlistparser.parsers.*` logger names — configure logging at the root
    # (or route through structlog with `structlog.stdlib.LoggerFactory()`).
    pl = PlaylistParser(
        "history.csv",
        require=["title", "artist"],
        default_artist="Unknown Artist",
        # as_type=PlaylistType.ENGINE,  # uncomment to bypass detection
    )

    # Detected format (PlaylistType enum: ENGINE, REKORDBOX, SERATO,
    # TRAKTOR, VIRTUALDJ). For .csv this triggers a one-time header sniff.
    print(f"Format: {pl.format.name}")

    # Stream tracks. Iteration is lazy — each pass re-reads the file unless
    # you materialise with .to_list() (cached for the lifetime of the parser).
    for track in pl:
        # str(track) → "Artist - Title"
        print(track)

        # Track is a frozen dataclass with these fields (all always present;
        # unsupported / missing values are 0 or ""):
        #   title: str, artist: str, file_path: str
        #   duration: int (seconds), year: int, bpm: int
        print(track.bpm, track.year, track.duration_str())  # e.g. "128 2024 6:42"

        # Serialise for JSON / DB. no_meta=True keeps only title + artist.
        payload = track.as_dict()

    # Aggregates materialise the full list once and cache it.
    print(f"{pl.track_count} tracks, {pl.total_duration}s total")

    # Explicit materialisation if you need the list directly.
    tracks = pl.to_list()

except UnknownFormatError as e:
    # Extension not recognised, or CSV header didn't match any known format.
    # Pass as_type=PlaylistType.X to override.
    print(f"Unsupported file: {e}")

except MissingFieldError as e:
    # A required field was missing — either unsupported by the format
    # (raised before parsing) or absent on a specific row.
    # e.field, e.line, e.track_title are available for diagnostics.
    print(f"Missing '{e.field}' on line {e.line}: {e.track_title!r}")

except MalformedPlaylistError as e:
    # Structural problem with the file (bad XML, truncated row, etc).
    # e.path and e.line locate the problem.
    print(f"Corrupt playlist: {e}")

except PlaylistParserError as e:
    # Base class — catch this if you don't care which of the above fired.
    print(f"Could not parse playlist: {e}")

except FileNotFoundError:
    # The library does not check existence in the constructor; the file is
    # opened on the first iteration / aggregate access.
    print("Playlist file does not exist")
```

### Supported formats and fields

| Format    | title | artist | duration | year | bpm | file_path |
| --------- | :---: | :----: | :------: | :--: | :-: | :-------: |
| Engine DJ |   x   |   x    |    x     |  x   |  x  |     x     |
| Rekordbox |   x   |   x    |    x     |  x   |  x  |     x     |
| Serato    |   x   |   x    |          |  x   |     |           |
| Traktor   |   x   |   x    |    x     |  x   |  x  |           |
| VirtualDJ |   x   |   x    |    x     |  x   |  x  |           |

## Developing

- `uv run ruff format` - format
- `uv run ruff check --fix --extend-fixable F401` - lint
- `uv run pytest` - run test suite
- `uv run ty check` - typecheck

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
