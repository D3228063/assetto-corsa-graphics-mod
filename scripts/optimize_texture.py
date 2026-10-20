#!/usr/bin/env python3
"""Losslessly recompress a PNG without removing image or color-profile data."""

import argparse
import os
import struct
import tempfile
import zlib
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def optimize_png(source, destination, force=False):
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if source == destination:
        raise ValueError("Source and destination must be different files")
    if destination.exists() and not force:
        raise FileExistsError(f"{destination} exists; pass --force to overwrite it")

    data = source.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("Input is not a PNG file")

    chunks = []
    idat_parts = []
    idat_insert_index = None
    offset = len(PNG_SIGNATURE)
    seen_idat = False
    idat_ended = False
    seen_iend = False
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4:offset + 8]
        end = offset + 8 + length
        if end + 4 > len(data):
            raise ValueError("Truncated PNG chunk data")
        payload = data[offset + 8:end]
        checksum = struct.unpack_from(">I", data, end)[0]
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != checksum:
            raise ValueError(f"Invalid CRC in {chunk_type.decode('ascii', errors='replace')} chunk")
        if not chunks and chunk_type != b"IHDR":
            raise ValueError("PNG must start with an IHDR chunk")
        if chunk_type == b"IDAT":
            if idat_ended:
                raise ValueError("PNG IDAT chunks must be consecutive")
            seen_idat = True
            idat_parts.append(payload)
        else:
            if seen_idat:
                idat_ended = True
                if idat_insert_index is None:
                    idat_insert_index = len(chunks)
            if chunk_type == b"IEND":
                if length != 0:
                    raise ValueError("PNG IEND chunk must be empty")
                seen_iend = True
            chunks.append((chunk_type, payload))
        offset = end + 4
        if seen_iend:
            if offset != len(data):
                raise ValueError("Unexpected data after PNG IEND")
            break

    if not seen_iend or not idat_parts:
        raise ValueError("PNG is missing IDAT or IEND")
    try:
        image_data = zlib.decompress(b"".join(idat_parts))
    except zlib.error as error:
        raise ValueError(f"Invalid PNG image data: {error}") from error

    compressor = zlib.compressobj(level=9)
    compressed = compressor.compress(image_data) + compressor.flush()
    output = bytearray(PNG_SIGNATURE)
    for index, (chunk_type, payload) in enumerate(chunks):
        if index == idat_insert_index:
            output.extend(make_chunk(b"IDAT", compressed))
        output.extend(make_chunk(chunk_type, payload))

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as file:
            temporary = Path(file.name)
            file.write(output)
        if destination.exists() and not force:
            raise FileExistsError(f"{destination} exists; pass --force to overwrite it")
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return len(data), len(output)


def make_chunk(chunk_type, payload):
    checksum = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", checksum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="source PNG texture")
    parser.add_argument("output", nargs="?", help="output PNG (defaults to <name>.optimized.png)")
    parser.add_argument("--force", action="store_true", help="allow replacing an existing output file")
    args = parser.parse_args()
    source = Path(args.input)
    destination = Path(args.output) if args.output else source.with_name(f"{source.stem}.optimized.png")
    try:
        before, after = optimize_png(source, destination, args.force)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    saved = before - after
    print(f"{destination}: {before} -> {after} bytes ({saved:+} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
