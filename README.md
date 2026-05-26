# Playlistparser

Tool for parsing DJ software playlists. Currently supports Engine DJ, Rekordbox, Serato, Traktor,
and VirtualDJ. Part of [Slipmat.io](https://slipmat.io) tools.

Free hosted version of this tool:
[https://slipmat.io/tools/playlist-converter/](https://slipmat.io/tools/playlist-converter/)

## Installing

`uv add playlistparser`

## Usage

```python
from playlistparser import PlaylistParser
```

### Stream tracks (default)

```python
for track in PlaylistParser("set.nml"):
    print(track)          # "Artist - Title"
    print(track.bpm, track.duration, track.year)
```

### Materialise into a list

```python
tracks = PlaylistParser("set.nml").to_list()
```

### Format detection and aggregates

```python
pl = PlaylistParser("history.csv")
print(pl.format)          # PlaylistType.SERATO / ENGINE / VIRTUALDJ (sniffed lazily)
print(pl.track_count)     # materialises once, cached thereafter
print(pl.total_duration)  # sum of track durations in seconds
```

### Enforce required fields

Raise `MissingFieldError` as soon as a row is missing one of the listed fields:

```python
from playlistparser import PlaylistParser, MissingFieldError

try:
    for track in PlaylistParser("set.nml", require=["title", "bpm", "year"]):
        ...
except MissingFieldError as e:
    print(f"Bad row: {e}")
```

If the format itself doesn't expose a required field (e.g. Serato has no `bpm`),
`MissingFieldError` is raised immediately — no parsing happens.

### Override format detection

```python
from playlistparser import PlaylistParser, PlaylistType

for track in PlaylistParser("export.dat", as_type=PlaylistType.ENGINE):
    ...
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
