# Refactor playlistparser public API to a single Playlist class

Collapse the package's public surface so `Playlist` is the only entry point. Streaming via
`__iter__` is the default, `.to_list()` is the explicit eager escape hatch, and detection /
aggregates are properties on the same object. The module-level `parse()`, `iter_tracks()`, and
`detect_format()` functions are removed.

## Current State

`playlistparser/__init__.py` exposes a class (`PlaylistParser`) plus three module-level functions
that wrap it (`parse`, `iter_tracks`, `detect_format`). The class itself has two names for the
format (`as_type`, `playlist_type`), two names for materialised tracks (`tracks` property,
`cached_tracks` cache attribute), and a `__len__` that overlaps with what the user spec calls
`track_count`. The README pushes `parse()` (eager, allocates) as the default usage example, with
`iter_tracks` documented separately as a streaming variant — the eager path is the easy one to
reach, the streaming path requires a second named import.

Affected components:

- `playlistparser/__init__.py` — full rewrite of the public surface
- `tests/test_main.py` — all `pp.parse`, `pp.iter_tracks`, `pp.detect_format`, `PlaylistParser`,
  `.tracks`, `.cached_tracks`, `.playlist_type`, `.as_type`, `len(p)`, `as_type=` references
- `tests/test_parsers.py` — every `pp.parse(...)` call (≥30 sites)
- `README.md` — the entire Usage section
- `CHANGES.md` — the 4.0.0 entry (not yet released, line items describe the now-removed functions)
- `playlistparser/exceptions.py` — `UnknownFormatError`'s message references `as_type=`

Per-format generators in `playlistparser/parsers/*.py` are untouched: they already are the
streaming primitives the new `Playlist` class drives.

## References

- Current public API: `playlistparser/__init__.py:1-243`
- `PlaylistParser` class: `playlistparser/__init__.py:76-172`
- Module-level convenience functions (to remove): `playlistparser/__init__.py:175-226`
- Existing exception types: `playlistparser/exceptions.py`
- Per-format streaming parsers (unchanged): `playlistparser/parsers/{engine,rekordbox,serato,traktor,virtualdj}.py`
- Tests using old API: `tests/test_main.py`, `tests/test_parsers.py`
- Project QA commands: `CLAUDE.md`, `AGENTS.md`
- Ruff config (note `A` rule for builtin shadowing): `pyproject.toml:62-131`

## Desired Outcome

A user installing the package and reading the README sees one import and one class. Streaming is
free, eagerness is explicit, aggregates are attributes.

```python
from playlistparser import Playlist

# default: stream
for track in Playlist("set.nml"):
    process(track)

# explicit materialisation
tracks = Playlist("set.nml").to_list()

# aggregates / detection — no separate import
pl = Playlist("set.nml")
pl.format         # PlaylistType.TRAKTOR
pl.track_count
pl.total_duration

# enforce required fields
for track in Playlist("set.nml", require=["bpm", "year"]):
    ...

# override detection for a misnamed file
Playlist("export.dat", format=PlaylistType.ENGINE)
```

Exception contract is unchanged from current behaviour, just reachable through the class:

- `UnknownFormatError` — raised by `Playlist(path)` for unsupported extensions; raised lazily on
  the first iteration / `.format` access for unrecognised CSV shapes.
- `MissingFieldError` — raised from iteration when a `require=`d field is missing on a consumed
  row; raised immediately on iteration when `require=` names a field the detected format cannot
  expose (e.g. `bpm` on Serato).
- Malformed individual rows continue to be logged at DEBUG and skipped.
- `PlaylistParserError` remains the catch-all base.

In scope: public-API rewrite, test migration, README and CHANGES rewrites. Out of scope:
per-format parser logic, `Track` dataclass, exception classes themselves, version bump beyond the
existing 4.0.0 (which has not yet shipped).

Public `__all__` after the refactor:

```
FieldName, MalformedPlaylistError, MissingFieldError, Playlist, PlaylistParserError,
PlaylistType, Track, UnknownFormatError
```

## Implementation Steps

Notes before executing these steps:

- Overall quality and sane architecture is the north star, not this document.
- Steps describe what to achieve, not exactly how. Use judgment.
- If a cleaner approach is obvious, raise it before taking it — the plan may have ruled it out for
  reasons not captured here.
- If a step looks wrong against the actual code, stop and ask. Do not force it.
- The target is the Desired Outcome. These steps are a route, not the destination.

### 1. Rewrite `playlistparser/__init__.py` around a single `Playlist` class

In `playlistparser/__init__.py`, replace the current `PlaylistParser` class plus the module-level
`parse`, `iter_tracks`, `detect_format`, `resolve_format`, and `sniff_csv` functions with one
`Playlist` class and a small set of private module helpers.

The class must:

- Accept the same constructor inputs as today's `PlaylistParser`, with `as_type=` renamed to
  `format=`. Final signature: `Playlist(path, *, require=(), format=None, logger=None,
  default_artist="Unknown Artist")`. Path accepts `str | os.PathLike[str]`.
- Resolve format eagerly for `.nml` and `.txt`; defer CSV sniffing until the `format` property is
  first read or iteration begins (same lazy behaviour as today's `playlist_type`). An explicit
  `format=` constructor argument bypasses detection entirely.
- Expose `format: PlaylistType` (replaces both `as_type` and `playlist_type`),
  `track_count: int`, and `total_duration: int` as properties. `track_count` and `total_duration`
  trigger a one-time materialisation and reuse a private cache on subsequent reads.
- Define `__iter__` that yields tracks straight from the per-format generator. Iteration is
  always a fresh streaming pass — it does **not** read from or populate the materialisation
  cache. This preserves today's streaming guarantee that unconsumed rows are not validated.
- Define `to_list() -> list[Track]` as the only public way to materialise. It populates the same
  private cache used by `track_count` / `total_duration`, so calling `to_list()` then accessing
  `track_count` does not re-read the file.
- **Not** define `__len__`; `track_count` is the single name for "how many tracks".
- **Not** expose `tracks`, `cached_tracks`, `stream`, `as_type`, or `playlist_type` — these names
  must disappear from the class.

Drop the following from the module entirely:

- `parse()`, `iter_tracks()`, `detect_format()` (module-level)
- `resolve_format()` — fold its logic into the class or into a private `_resolve_format` helper
- `sniff_csv()` — rename to a private `_sniff_csv`

Update `__all__` to the eight names listed in Desired Outcome.

The `format=` keyword argument shadows the built-in `format`. Suppress ruff `A002` on that one
argument (inline `# noqa: A002` on the signature line, not a per-file ignore). The property name
also shadows the builtin but is on a class and not flagged.

### 2. Update `UnknownFormatError` message to reference `format=`

In `playlistparser/exceptions.py:19`, change the trailing sentence from `"Use the as_type=
parameter to override detection."` to reference `format=` instead. The existing
`test_unknown_error_message_lists_extensions` and `test_detect_format_unknown` tests assert the
substring `"as_type="` — update those assertions in the test migration step.

### 3. Migrate `tests/test_main.py` to the new API

Rewrite every reference to the old public surface:

- `from playlistparser import PlaylistParser` → `from playlistparser import Playlist`
- `pp.parse(path, ...)` → `Playlist(path, ...).to_list()`
- `pp.iter_tracks(path, ...)` → `iter(Playlist(path, ...))` (the streaming test must still call
  `next()` on the returned iterator)
- `pp.detect_format(path)` → `Playlist(path).format`
- `PlaylistParser(...)` → `Playlist(...)`
- `.playlist_type` and `.as_type` → `.format`
- `len(p)` → `p.track_count`
- `p.tracks` (list access) → `p.to_list()`
- `as_type=` keyword → `format=`
- Substring assertion `"as_type="` in `test_detect_format_unknown` and
  `test_unknown_error_message_lists_extensions` → `"format="`

The `test_playlist_parser_tracks_lazy` test currently inspects `p.cached_tracks` directly. Since
the cache is private after the refactor, replace it with an observable behaviour check: assert
that `p.track_count` returns a positive integer and that a second `to_list()` call returns the
same list identity (or at minimum, equal contents — pick whichever the implementation supports
without exposing internals).

Remove the existing block comments `# detect_format` and `# PlaylistParser` and replace with
`# Playlist` section headers as appropriate.

### 4. Migrate `tests/test_parsers.py` to the new API

Replace every `pp.parse(path, ...)` call with `Playlist(path, ...).to_list()`. No other public-API
surface is used in this file — `import playlistparser as pp` and `from playlistparser import
MissingFieldError` stay, but the `pp.` reference set collapses to nothing, so change the import
to `from playlistparser import Playlist, MissingFieldError` and drop the `pp` alias.

### 5. Rewrite the README Usage section

In `README.md`, replace the three current usage blocks (`parse`, `iter_tracks`, `PlaylistParser`)
with a single block that introduces `Playlist`. The new section must show, in this order:
streaming iteration (default), `.to_list()` for explicit materialisation, accessing `.format` /
`.track_count` / `.total_duration` properties, `require=` enforcement, and `format=` detection
override. The section that currently shows `detect_format` becomes a one-liner under the
properties example. Keep the Supported formats table and everything below Developing untouched.

### 6. Update `CHANGES.md` 4.0.0 entry

The 4.0.0 entry in `CHANGES.md:3-18` currently describes the now-removed `parse()`,
`iter_tracks()`, and `detect_format()` as features. Rewrite that entry to describe the actual
shipped public surface: single `Playlist` class with `__iter__`-by-default, `to_list()`,
`format`, `track_count`, `total_duration`, `require=`, and `format=` override. Keep the
"Breaking" bullets that describe the v3 → v4 changes that are still accurate (parsers became
streaming, the old `require_*` booleans were dropped). Do not add a new version entry — 4.0.0
has not yet shipped.

### 7. Tests for the new API

First read `CLAUDE.md` and `AGENTS.md` for QA conventions and skim the migrated `test_main.py`
and `test_parsers.py` to match style (pytest function-style, `tmp_path` for synthetic files,
parametrize where format-symmetric).

The migration in steps 3 and 4 already covers basic shape (construction, iteration, list
materialisation, properties, require=, format= override, error messages). Add targeted tests
**only** for behaviours that are new contracts of the refactored class, not already covered by
the migrated tests:

- Iterating a `Playlist` twice with `for track in pl: ...` re-reads the file each time (fresh
  streaming pass) — assert by mutating a counter or comparing iteration outputs from two
  consecutive loops on the same `Playlist` instance.
- Calling `to_list()` twice returns equal contents and does not re-parse the file on the second
  call (observable via the same logger-capture trick used in `test_logger_receives_records`, or
  by patching the per-format `iter_tracks` import and asserting call count).
- `track_count` and `total_duration` accessed after `to_list()` share the cache (no extra parse).
- Construction with `format=PlaylistType.ENGINE` on a `.dat` file (currently rejected by
  extension) succeeds and yields the expected tracks — confirms the rename from `as_type=`
  preserves the override-extension behaviour.

Do not add per-field require= tests or per-format parse tests — those already exist in the
migrated `test_parsers.py`. Target is a small, behaviour-focused addition, not coverage chasing.

### 8. QA

Run

- `uv run ruff format`
- `uv run ruff check --fix --extend-fixable F401`
- `uv run ty check`
- `uv run pytest`

Fix ALL reported issues. No exceptions.
