#!/usr/bin/env python3
"""Record and validate locally compiled default model artifacts.

This module intentionally depends only on the Python standard library and the
chunked-file helpers. It runs during the native build before compiled Python
extensions are guaranteed to exist and from stripped local prebuilts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openpilot.common.file_chunker import get_manifest_path, open_file_chunked


MAX_CHUNK_SIZE = 100 * 1024 * 1024


@dataclass(frozen=True)
class ModelSpec:
  target: str
  onnx: str
  canonical: str
  backend: str


MODEL_SPECS = {
  "small": ModelSpec("small", "driving_supercombo.onnx", "driving_tinygrad.pkl", "QCOM"),
  "big": ModelSpec("big", "big_driving_supercombo.onnx", "big_driving_tinygrad.pkl", "AMD"),
  "dm": ModelSpec("dm", "dmonitoring_model.onnx", "dmonitoring_model_tinygrad.pkl", "QCOM"),
}


def _git_blob(repo_root: Path, path: str) -> bytes | None:
  try:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=repo_root, stderr=subprocess.DEVNULL)
  except (OSError, subprocess.CalledProcessError):
    return None


def onnx_sha256(repo_root: Path, relative_path: str) -> str:
  """Return the content hash, using the LFS pointer when one is available."""
  pointer = _git_blob(repo_root, f"openpilot/selfdrive/modeld/models/{relative_path}")
  if pointer is not None:
    try:
      for line in pointer.decode("ascii").splitlines():
        if line.startswith("oid sha256:"):
          digest = line.removeprefix("oid sha256:").strip()
          if re.fullmatch(r"[0-9a-f]{64}", digest):
            return digest
    except UnicodeDecodeError:
      pass

  path = repo_root / "openpilot/selfdrive/modeld/models" / relative_path
  digest = hashlib.sha256()
  with open_file_chunked(str(path)) as source:
    while block := source.read(1024 * 1024):
      digest.update(block)
  return digest.hexdigest()


def tinygrad_ref(repo_root: Path) -> str:
  try:
    return subprocess.check_output(["git", "rev-parse", "HEAD:tinygrad_repo"], cwd=repo_root,
                                   stderr=subprocess.DEVNULL, text=True).strip()
  except (OSError, subprocess.CalledProcessError) as e:
    raise RuntimeError("could not resolve tinygrad revision") from e


def _hash_file(path: Path) -> str:
  digest = hashlib.sha256()
  with open(path, "rb") as source:
    while block := source.read(1024 * 1024):
      digest.update(block)
  return digest.hexdigest()


def _metadata_path(destination: Path, canonical: str) -> Path:
  return destination / f"{canonical}.metadata.json"


def _chunk_paths(destination: Path, canonical: str, count: int) -> list[Path]:
  return [destination / f"{canonical}.chunk{i:02d}of{count:02d}" for i in range(1, count + 1)]


def validate_artifact_files(destination: Path, spec: ModelSpec) -> tuple[bool, str]:
  manifest = Path(get_manifest_path(str(destination / spec.canonical)))
  try:
    count = int(manifest.read_text().strip())
  except (OSError, ValueError):
    return False, f"missing or invalid manifest for {spec.target}"
  if count < 1 or count > 1000:
    return False, f"invalid chunk count for {spec.target}: {count}"

  total_size = 0
  expected = _chunk_paths(destination, spec.canonical, count)
  for path in expected:
    if not path.is_file():
      return False, f"missing chunk for {spec.target}: {path.name}"
    try:
      size = path.stat().st_size
    except OSError:
      return False, f"unreadable chunk for {spec.target}: {path.name}"
    if size > MAX_CHUNK_SIZE:
      return False, f"invalid chunk size for {spec.target}: {path.name}"
    total_size += size
  if total_size == 0:
    return False, f"empty chunk set for {spec.target}"

  expected_names = {path.name for path in expected}
  for path in destination.glob(f"{spec.canonical}.chunk*"):
    if re.fullmatch(re.escape(spec.canonical) + r"\.chunk\d+of\d+", path.name) and path.name not in expected_names:
      return False, f"unexpected stale chunk for {spec.target}: {path.name}"
  return True, "ok"


def _metadata_source(destination: Path, spec: ModelSpec) -> str | None:
  try:
    source = json.loads(_metadata_path(destination, spec.canonical).read_text()).get("source")
    return source if isinstance(source, str) else None
  except (OSError, TypeError, ValueError, json.JSONDecodeError):
    return None


def local_artifact_valid(destination: Path, spec: ModelSpec, onnx_hash: str, tg_ref: str,
                         required_source: str | None = None) -> bool:
  try:
    metadata = json.loads(_metadata_path(destination, spec.canonical).read_text())
    if (metadata.get("schema"), metadata.get("target"), metadata.get("canonical"), metadata.get("onnx_sha256"),
        metadata.get("tinygrad_ref"), metadata.get("backend")) != \
       (1, spec.target, spec.canonical, onnx_hash, tg_ref, spec.backend):
      return False
    if required_source is not None and metadata.get("source") != required_source:
      return False
    chunks = metadata["chunks"]
    if not isinstance(chunks, list) or not chunks:
      return False
    expected = _chunk_paths(destination, spec.canonical, len(chunks))
    for path, expected_meta in zip(expected, chunks, strict=True):
      if path.name != expected_meta["name"] or not path.is_file() or path.stat().st_size > MAX_CHUNK_SIZE:
        return False
      if path.stat().st_size != expected_meta["size"] or _hash_file(path) != expected_meta["sha256"]:
        return False
    valid, _ = validate_artifact_files(destination, spec)
    manifest = Path(get_manifest_path(str(destination / spec.canonical)))
    return valid and manifest.read_text().strip() == str(len(chunks))
  except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
    return False


def _remove_obsolete_chunks(destination: Path, spec: ModelSpec, expected: set[str]) -> None:
  for path in destination.glob(f"{spec.canonical}.chunk*"):
    if re.fullmatch(re.escape(spec.canonical) + r"\.chunk\d+of\d+", path.name) and path.name not in expected:
      path.unlink(missing_ok=True)


def write_local_metadata(repo_root: Path, target: str) -> None:
  spec = MODEL_SPECS[target]
  destination = repo_root / "openpilot/selfdrive/modeld/models"
  manifest = Path(get_manifest_path(str(destination / spec.canonical)))
  count = int(manifest.read_text().strip())
  paths = _chunk_paths(destination, spec.canonical, count)
  _remove_obsolete_chunks(destination, spec, {path.name for path in paths})
  valid, detail = validate_artifact_files(destination, spec)
  if not valid:
    raise RuntimeError(detail)

  metadata: dict[str, Any] = {
    "schema": 1,
    "target": target,
    "canonical": spec.canonical,
    "backend": spec.backend,
    "onnx_sha256": onnx_sha256(repo_root, spec.onnx),
    "tinygrad_ref": tinygrad_ref(repo_root),
    "source": "local",
    "chunks": [{"name": path.name, "size": path.stat().st_size, "sha256": _hash_file(path)} for path in paths],
  }
  metadata_path = _metadata_path(destination, spec.canonical)
  temporary = metadata_path.with_name(f".{metadata_path.name}.tmp")
  temporary.write_text(json.dumps(metadata, sort_keys=True) + "\n")
  os.replace(temporary, metadata_path)


def validate_targets(destination: Path, targets: list[str], required_source: str | None = None) -> dict[str, Any]:
  results = []
  for target in targets:
    spec = MODEL_SPECS[target]
    valid, detail = validate_artifact_files(destination, spec)
    if valid:
      try:
        metadata = json.loads(_metadata_path(destination, spec.canonical).read_text())
        chunks = metadata["chunks"]
        expected = _chunk_paths(destination, spec.canonical, len(chunks))
        manifest_count = int(Path(get_manifest_path(str(destination / spec.canonical))).read_text().strip())
        valid = ((metadata.get("schema"), metadata.get("target"), metadata.get("canonical"), metadata.get("backend")) ==
                 (1, spec.target, spec.canonical, spec.backend) and
                 (required_source is None or metadata.get("source") == required_source) and
                 len(expected) == len(chunks) == manifest_count and
                 all(path.name == item["name"] and path.stat().st_size == item["size"] and
                     _hash_file(path) == item["sha256"] for path, item in zip(expected, chunks, strict=True)))
        if not valid:
          detail = f"invalid or non-local metadata for {target}"
      except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
        valid, detail = False, f"missing or invalid metadata for {target}"
    results.append({"target": target, "valid": valid, "detail": detail})
  return {"results": results, "valid": all(result["valid"] for result in results)}


def validate_compatible_targets(repo_root: Path, destination: Path, targets: list[str],
                                required_source: str | None = None) -> dict[str, Any]:
  results = []
  for target in targets:
    spec = MODEL_SPECS[target]
    try:
      onnx_hash = onnx_sha256(repo_root, spec.onnx)
      tg_ref = tinygrad_ref(repo_root)
      valid = local_artifact_valid(destination, spec, onnx_hash, tg_ref, required_source)
      detail = "ok" if valid else f"incompatible, invalid, or non-local {target} artifact"
    except (OSError, RuntimeError, ValueError) as e:
      valid, detail = False, str(e)
      onnx_hash, tg_ref = None, None
    results.append({"target": target, "valid": valid, "detail": detail,
                    "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref,
                    "source": _metadata_source(destination, spec)})
  return {"results": results, "valid": all(result["valid"] for result in results)}


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Validate locally compiled default model artifacts")
  parser.add_argument("--repo-root", default=".")
  parser.add_argument("--targets", nargs="+", choices=sorted(MODEL_SPECS), default=["small", "dm", "big"])
  parser.add_argument("--destination")
  parser.add_argument("--validate", action="store_true")
  parser.add_argument("--compatible", action="store_true", help="also verify ONNX and tinygrad identity")
  parser.add_argument("--locally-built", action="store_true", help="require metadata written by local compilation")
  args = parser.parse_args(argv)
  if not args.validate:
    parser.error("only validation is supported")
  repo_root = Path(args.repo_root).resolve()
  destination = Path(args.destination).resolve() if args.destination else repo_root / "openpilot/selfdrive/modeld/models"
  required_source = "local" if args.locally_built else None
  result = (validate_compatible_targets(repo_root, destination, args.targets, required_source)
            if args.compatible else validate_targets(destination, args.targets, required_source))
  print(json.dumps(result, sort_keys=True))
  return 0 if result["valid"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
