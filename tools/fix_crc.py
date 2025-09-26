#!/usr/bin/env python3
"""Recalculate CRC32 checksum trailers for SJA1110 firmware images.

Usage:
    ./tools/fix_crc.py path/to/sja1110_switch.bin [path/to/other.bin ...]
"""

from __future__ import annotations

import argparse
import sys
import zlib
from pathlib import Path


def fix_crc(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 4:
        raise ValueError(f"'{path}' is too small to contain a CRC32 trailer")

    payload, old_crc_bytes = data[:-4], data[-4:]
    new_crc = zlib.crc32(payload) & 0xFFFFFFFF

    if int.from_bytes(old_crc_bytes, "little") == new_crc:
        print(f"✓ {path} already has CRC32 0x{new_crc:08x}")
        return

    path.write_bytes(payload + new_crc.to_bytes(4, "little"))
    print(f"✓ Updated {path} CRC32 to 0x{new_crc:08x}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="binary files to patch")
    args = parser.parse_args(argv)

    for file_name in args.files:
        fix_crc(Path(file_name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
