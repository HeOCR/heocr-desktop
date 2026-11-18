"""A minimal OLE2 (Compound File Binary) writer for identification fixtures.

It writes a valid header, one FAT sector and a directory of empty streams. That is
enough for content-based identification; it is not a full CFB implementation.
"""

from __future__ import annotations

import struct

_END, _FREE, _FATSECT = 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD
_NOSTREAM = 0xFFFFFFFF


def _entry(name: str, kind: int, child: int = _NOSTREAM, right: int = _NOSTREAM) -> bytes:
    encoded = name.encode("utf-16-le") + b"\x00\x00"
    entry = bytearray(128)
    entry[: len(encoded)] = encoded
    struct.pack_into("<H", entry, 64, len(encoded))
    entry[66] = kind
    entry[67] = 1  # black
    struct.pack_into("<III", entry, 68, _NOSTREAM, right, child)
    struct.pack_into("<II", entry, 116, _END, 0)  # start sector, size
    return bytes(entry)


def make_cfb(stream_names: list[str]) -> bytes:
    entries = [_entry("Root Entry", 5, child=1 if stream_names else _NOSTREAM)]
    for i, name in enumerate(stream_names):
        right = i + 2 if i + 1 < len(stream_names) else _NOSTREAM
        entries.append(_entry(name, 2, right=right))
    while len(entries) % 4:
        entries.append(bytes(128))
    n_dir = len(entries) // 4

    header = bytearray(512)
    header[:8] = bytes.fromhex("d0cf11e0a1b11ae1")
    struct.pack_into("<HHHH", header, 24, 0x3E, 3, 0xFFFE, 9)  # minor, major, byte order, sector shift
    struct.pack_into("<H", header, 32, 6)
    struct.pack_into("<I", header, 44, 1)  # FAT sectors
    struct.pack_into("<I", header, 48, 1)  # first directory sector
    struct.pack_into("<I", header, 56, 4096)
    struct.pack_into("<III", header, 60, _END, 0, _END)  # mini FAT, DIFAT
    struct.pack_into("<II", header, 72, 0, 0)
    difat = [0] + [_FREE] * 108
    struct.pack_into("<109I", header, 76, *difat)

    fat = [_FATSECT] + [i + 1 for i in range(1, n_dir)] + [_END]
    fat += [_FREE] * (128 - len(fat))
    fat_sector = struct.pack("<128I", *fat)
    return bytes(header) + fat_sector + b"".join(entries)
