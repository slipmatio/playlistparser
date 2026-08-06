import logging
from functools import partial
from typing import TYPE_CHECKING

from lxml import etree

from playlistparser.exceptions import MalformedPlaylistError, MissingFieldError
from playlistparser.track import Track, normalize_text
from playlistparser.utils import required

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import BinaryIO

    from playlistparser import FieldName

logger = logging.getLogger(__name__)


def entries_count(element: etree._Element) -> int | None:
    """Read a non-negative ENTRIES attribute, or None when it is absent or junk."""
    raw_total = element.get("ENTRIES")
    if raw_total is None:
        return None
    try:
        total = int(raw_total)
    except ValueError:
        return None
    return total if total >= 0 else None


def track_total(file: BinaryIO) -> int | None:
    """Return how many tracks :func:`iter_tracks` will yield, when the NML says so.

    Tracks are yielded in PLAYLIST order, so the PLAYLIST entry counts are the
    real total; COLLECTION ENTRIES is only the fallback for files without a
    PLAYLIST node.  ENTRY subtrees are cleared as they close to keep this
    pre-pass from building the whole document in memory.
    """
    context = etree.iterparse(file, events=("start", "end"), tag=("COLLECTION", "PLAYLIST", "ENTRY"))
    collection_total: int | None = None
    playlist_total = 0
    playlist_seen = False
    try:
        for event, element in context:
            if element.tag == "ENTRY":
                if event == "end":
                    element.clear()
                continue
            if event != "start":
                continue
            if element.tag == "COLLECTION":
                collection_total = entries_count(element)
                continue
            playlist_seen = True
            total = entries_count(element)
            if total is None:
                return None
            playlist_total += total
    except etree.XMLSyntaxError:
        return None
    finally:
        del context
    return playlist_total if playlist_seen else collection_total


def location_key(location: etree._Element) -> str:
    """Build the ``VOLUME/:DIR/:FILE`` key that PLAYLIST PRIMARYKEYs reference."""
    volume = location.get("VOLUME") or ""
    directory = location.get("DIR") or ""
    filename = location.get("FILE") or ""
    return normalize_text(f"{volume}{directory}{filename}")


def attribute(element: etree._Element | None, name: str) -> str:
    """Return a stripped attribute value, tolerating a missing element."""
    return "" if element is None else (element.get(name) or "").strip()


def entry_key(elem: etree._Element) -> str:
    """Return the PRIMARYKEY lookup key of a COLLECTION ENTRY, without building the Track."""
    location = elem.find("LOCATION")
    return "" if location is None else location_key(location)


def build_track(
    elem: etree._Element,
    entry: int,
    require: frozenset[FieldName],
    default_artist: str,
) -> tuple[str, Track]:
    """Build a Track from one COLLECTION ENTRY, plus its PRIMARYKEY lookup key."""
    track_title = required(attribute(elem, "TITLE"), "title", require, line=entry)
    field = partial(required, require=require, line=entry, track_title=track_title)

    track_artist = field(attribute(elem, "ARTIST"), "artist") or default_artist
    album = field(attribute(elem.find("ALBUM"), "TITLE"), "album")
    vendor_id = field(attribute(elem, "AUDIO_ID"), "vendor_id")

    meta = elem.find("INFO")
    year = field(attribute(meta, "RELEASE_DATE"), "year")
    key = field(attribute(meta, "KEY"), "key")
    try:
        playtime = int(attribute(meta, "PLAYTIME") or 0)
    except ValueError:
        playtime = 0
    field(playtime, "duration")

    try:
        bpm = float(attribute(elem.find("TEMPO"), "BPM") or 0.0)
    except ValueError:
        bpm = 0.0
    field(bpm, "bpm")

    location = elem.find("LOCATION")
    track_path = ""
    primary_key = ""
    if location is not None:
        directory = attribute(location, "DIR").replace("/:", "/")
        track_path = f"{directory}{location.get('FILE') or ''}"
        primary_key = location_key(location)
    field(track_path, "file_path")

    return primary_key, Track(
        title=track_title,
        artist=track_artist,
        album=album,
        key=key,
        year=year,
        duration=playtime,
        bpm=bpm,
        file_path=track_path,
        vendor_id=vendor_id,
    )


def iter_tracks(
    file: BinaryIO,
    *,
    require: frozenset[FieldName] = frozenset(),
    default_artist: str = "Unknown Artist",
) -> Iterator[Track]:
    """Traktor NML supports: title, artist, album, key, year, duration, bpm, file_path, vendor_id.

    COLLECTION is an unordered track database; the PLAYLIST node holds the set
    order as PRIMARYKEY references.  Tracks are therefore yielded in PLAYLIST
    order, which means the collection is held in memory until the PLAYLISTS
    section is reached.  Files without a PLAYLIST node fall back to COLLECTION
    order.

    A collection track is only validated against *require* once the playlist
    selects it, so an unrelated library track missing a required field cannot
    abort the parse.

    Yields one :class:`~playlistparser.track.Track` per playlist entry.
    """
    context = etree.iterparse(file, events=("end",), tag=("ENTRY", "PLAYLIST"))
    collection: dict[str, Track | MissingFieldError] = {}
    collection_order: list[Track | MissingFieldError] = []
    playlist_seen = False
    entry = 0

    try:
        for event, elem in context:
            del event  # iterparse event string; only "end" is used here
            if elem.tag == "PLAYLIST":
                # Even an empty PLAYLIST is a selection: the collection is not a fallback for it.
                playlist_seen = True
                elem.clear()
                continue

            entry += 1
            primarykey = elem.find("PRIMARYKEY")
            if primarykey is not None:
                key = normalize_text(primarykey.get("KEY") or "")
                track = collection.get(key)
                if track is None:
                    logger.warning("Playlist entry %d references an unknown track: %s", entry, key)
                elif isinstance(track, MissingFieldError):
                    raise track
                else:
                    yield track
                elem.clear()
                continue

            # Neither a collection track nor a playlist reference — skip it.
            if "TITLE" not in elem.attrib:
                elem.clear()
                continue

            try:
                key, track = build_track(elem, entry, require, default_artist)
            except MissingFieldError as exc:
                # Held back: a missing field only matters once the playlist selects this track.
                key, track = entry_key(elem), exc
            except (AttributeError, ValueError, TypeError) as exc:
                logger.debug("Skipping entry %d: %s", entry, exc)
                elem.clear()
                continue
            collection[key] = track
            collection_order.append(track)
            elem.clear()
    except etree.XMLSyntaxError as exc:
        raise MalformedPlaylistError(f"Invalid Traktor NML: {exc.msg}", line=exc.lineno) from exc

    if not playlist_seen:
        for track in collection_order:
            if isinstance(track, MissingFieldError):
                raise track
            yield track
