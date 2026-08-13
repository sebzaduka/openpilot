#!/usr/bin/env python3
import argparse
import hashlib
import lzma
import struct
from pathlib import Path


SPARSE_MAGIC = 0xED26FF3A
CHUNK_RAW = 0xCAC1
CHUNK_FILL = 0xCAC2
CHUNK_DONT_CARE = 0xCAC3
CHUNK_CRC32 = 0xCAC4
COPY_SIZE = 1024 * 1024


class HashingReader:
  def __init__(self, source):
    self.source = source
    self.sha256 = hashlib.sha256()

  def read_exact(self, size: int) -> bytes:
    data = self.source.read(size)
    if len(data) != size:
      raise EOFError(f"expected {size} bytes, got {len(data)}")
    self.sha256.update(data)
    return data


def write_repeated(output, raw_hash, value: bytes, size: int) -> None:
  block = (value * (COPY_SIZE // len(value) + 1))[:COPY_SIZE]
  while size:
    chunk = block[: min(size, len(block))]
    output.write(chunk)
    raw_hash.update(chunk)
    size -= len(chunk)


def extract(source_path: Path, output_path: Path, sparse_hash: str, raw_hash: str, raw_size: int) -> None:
  with lzma.open(source_path, "rb") as compressed, output_path.open("wb") as output:
    source = HashingReader(compressed)
    header = source.read_exact(28)
    magic, major, minor, file_header_size, chunk_header_size, block_size, total_blocks, total_chunks, _ = struct.unpack("<I4H4I", header)

    if magic != SPARSE_MAGIC or (major, minor) != (1, 0):
      raise ValueError("input is not a supported Android sparse image")
    if file_header_size < len(header) or chunk_header_size < 12:
      raise ValueError("invalid sparse-image header sizes")
    if file_header_size > len(header):
      source.read_exact(file_header_size - len(header))

    expanded_hash = hashlib.sha256()
    expanded_size = 0

    for index in range(total_chunks):
      chunk_header = source.read_exact(chunk_header_size)
      chunk_type, _, output_blocks, total_size = struct.unpack("<2H2I", chunk_header[:12])
      output_size = output_blocks * block_size
      payload_size = total_size - chunk_header_size

      if chunk_type == CHUNK_RAW:
        if payload_size != output_size:
          raise ValueError(f"raw chunk {index} has inconsistent size")
        remaining = payload_size
        while remaining:
          data = source.read_exact(min(remaining, COPY_SIZE))
          output.write(data)
          expanded_hash.update(data)
          remaining -= len(data)
      elif chunk_type == CHUNK_FILL:
        if payload_size != 4:
          raise ValueError(f"fill chunk {index} has invalid payload")
        write_repeated(output, expanded_hash, source.read_exact(4), output_size)
      elif chunk_type == CHUNK_DONT_CARE:
        if payload_size != 0:
          raise ValueError(f"don't-care chunk {index} has invalid payload")
        write_repeated(output, expanded_hash, b"\0", output_size)
      elif chunk_type == CHUNK_CRC32:
        if payload_size != 4 or output_size != 0:
          raise ValueError(f"CRC chunk {index} has invalid size")
        source.read_exact(4)
      else:
        raise ValueError(f"unsupported sparse chunk type 0x{chunk_type:04x}")

      expanded_size += output_size

    if expanded_size != total_blocks * block_size or expanded_size != raw_size:
      raise ValueError(f"expanded size mismatch: got {expanded_size}, expected {raw_size}")
    if source.sha256.hexdigest() != sparse_hash:
      raise ValueError(f"sparse SHA-256 mismatch: got {source.sha256.hexdigest()}")
    if expanded_hash.hexdigest() != raw_hash:
      raise ValueError(f"raw SHA-256 mismatch: got {expanded_hash.hexdigest()}")
    if compressed.read(1):
      raise ValueError("trailing data after sparse image")


def main() -> None:
  parser = argparse.ArgumentParser(description="Verify and expand an xz-compressed Android sparse image")
  parser.add_argument("source", type=Path)
  parser.add_argument("output", type=Path)
  parser.add_argument("--sparse-sha256", required=True)
  parser.add_argument("--raw-sha256", required=True)
  parser.add_argument("--raw-size", required=True, type=int)
  args = parser.parse_args()

  extract(args.source, args.output, args.sparse_sha256.lower(), args.raw_sha256.lower(), args.raw_size)


if __name__ == "__main__":
  main()
