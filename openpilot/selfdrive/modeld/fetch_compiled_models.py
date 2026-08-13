#!/usr/bin/env python3
"""Fetch compatible precompiled default model artifacts.

This module intentionally depends only on the Python standard library and the
chunked-file helpers.  It is run before the normal native build, when compiled
Python extensions are not guaranteed to exist yet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from openpilot.common.file_chunker import get_manifest_path, open_file_chunked


HF_REPO = os.getenv("HF_MODEL_REPO", "sunnypilot/sunnypilot_models_v1")
HF_BASE_URL = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"
METADATA_TIMEOUT = 15
CHUNK_TIMEOUT = 120
MAX_METADATA_SIZE = 16 * 1024 * 1024
MAX_CHUNK_SIZE = 100 * 1024 * 1024
CHUNK_RE = re.compile(r"(?:^|\.)chunk(?P<index>\d+)of(?P<count>\d+)$")
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ModelSpec:
  target: str
  onnx: str
  canonical: str
  hf_path: str
  backend: str


MODEL_SPECS = {
  "small": ModelSpec("small", "driving_supercombo.onnx", "driving_tinygrad.pkl", "small", "QCOM"),
  "big": ModelSpec("big", "big_driving_supercombo.onnx", "big_driving_tinygrad.pkl", "big", "AMD"),
  "dm": ModelSpec("dm", "dmonitoring_model.onnx", "dmonitoring_model_tinygrad.pkl", "dm", "QCOM"),
}


def _json_request(url: str, timeout: float) -> dict[str, Any]:
  request = Request(url, headers={"Accept": "application/json", "User-Agent": "openpilot-model-fetcher"})
  with urlopen(request, timeout=timeout) as response:
    data = response.read(MAX_METADATA_SIZE + 1)
  if len(data) > MAX_METADATA_SIZE:
    raise ValueError("remote model metadata is too large")
  parsed = json.loads(data)
  if not isinstance(parsed, dict):
    raise ValueError("remote model metadata is not an object")
  return parsed


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
      text = pointer.decode("ascii")
      for line in text.splitlines():
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


def _safe_remote_name(name: Any) -> str:
  if not isinstance(name, str) or not name or not SAFE_NAME_RE.fullmatch(name) or "/" in name or "\\" in name:
    raise ValueError(f"unsafe model chunk filename: {name!r}")
  return name


def _artifact_from_metadata(metadata: dict[str, Any], spec: ModelSpec, onnx_hash: str, tg_ref: str) -> dict[str, Any] | None:
  schema = metadata.get("schema")
  if schema is not None and schema != 1:
    raise ValueError(f"unsupported remote model metadata schema: {schema!r}")
  if metadata.get("tinygrad_ref") != tg_ref:
    return None
  bundles = metadata.get("bundles")
  if not isinstance(bundles, list):
    raise ValueError("remote model metadata has no bundle list")

  for bundle in bundles:
    if not isinstance(bundle, dict) or bundle.get("onnx_sha256") != onnx_hash:
      continue
    bundle_schema = bundle.get("schema")
    if bundle_schema is not None and bundle_schema != 1:
      raise ValueError(f"unsupported remote {spec.target} bundle schema: {bundle_schema!r}")
    if bundle.get("target") not in (None, spec.target):
      continue
    if bundle.get("backend") not in (None, spec.backend):
      continue
    if bundle.get("runner") not in (None, "tinygrad"):
      continue
    if "is_big" in bundle and bool(bundle["is_big"]) != (spec.target == "big"):
      continue
    models = bundle.get("models")
    if not isinstance(models, list) or not models or not isinstance(models[0], dict):
      raise ValueError(f"remote {spec.target} bundle has no model")
    artifact = models[0].get("artifact")
    if (models[0].get("type", "chunked") != "chunked" or
        not isinstance(artifact, dict)):
      raise ValueError(f"remote {spec.target} artifact is not chunked")
    if artifact.get("file_name") not in (None, spec.canonical):
      raise ValueError(f"remote {spec.target} artifact name does not match {spec.canonical}")
    chunks = artifact.get("chunks")
    if not isinstance(chunks, list) or not chunks:
      raise ValueError(f"remote {spec.target} artifact has no chunks")

    normalized: list[dict[str, Any]] = []
    seen: set[int] = set()
    total = len(chunks)
    for chunk in chunks:
      if not isinstance(chunk, dict):
        raise ValueError(f"remote {spec.target} chunk is not an object")
      remote_name = _safe_remote_name(chunk.get("file_name"))
      match = CHUNK_RE.search(remote_name)
      if match is None or int(match.group("count")) != total:
        raise ValueError(f"remote {spec.target} chunk numbering is invalid: {remote_name}")
      index = int(match.group("index"))
      if index < 1 or index > total or index in seen:
        raise ValueError(f"remote {spec.target} chunk index is invalid: {remote_name}")
      digest = chunk.get("sha256")
      if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError(f"remote {spec.target} chunk has no valid SHA-256: {remote_name}")
      url = chunk.get("url")
      if not isinstance(url, str):
        base = artifact.get("download_uri", {}).get("url") if isinstance(artifact.get("download_uri"), dict) else None
        if not isinstance(base, str):
          raise ValueError(f"remote {spec.target} chunk has no download URL: {remote_name}")
        url = base.rsplit("/", 1)[0] + "/" + remote_name
      parsed_url = urlparse(url)
      if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError(f"remote {spec.target} chunk URL is not HTTPS: {url!r}")
      seen.add(index)
      normalized.append({
        "index": index,
        "url": url,
        "sha256": digest,
        "name": f"{spec.canonical}.chunk{index:02d}of{total:02d}",
      })
    if seen != set(range(1, total + 1)):
      raise ValueError(f"remote {spec.target} chunk numbering is incomplete")
    normalized.sort(key=lambda c: c["index"])
    return {
      "target": spec.target,
      "canonical": spec.canonical,
      "backend": spec.backend,
      "onnx_sha256": onnx_hash,
      "tinygrad_ref": tg_ref,
      "chunks": normalized,
      "bundle": bundle,
    }
  return None


def resolve_remote(spec: ModelSpec, onnx_hash: str, tg_ref: str, timeout: float = METADATA_TIMEOUT,
                   metadata_url: str | None = None) -> dict[str, Any] | None:
  url = metadata_url or f"{HF_BASE_URL}/models/defaults/{spec.hf_path}/default_models.json"
  metadata = _json_request(url, timeout)
  return _artifact_from_metadata(metadata, spec, onnx_hash, tg_ref)


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
  """Validate a canonical chunk set without requiring sidecar metadata."""
  manifest = Path(get_manifest_path(str(destination / spec.canonical)))
  try:
    count_text = manifest.read_text().strip()
    count = int(count_text)
  except (OSError, ValueError):
    return False, f"missing or invalid manifest for {spec.target}"
  if count < 1 or count > 1000:
    return False, f"invalid chunk count for {spec.target}: {count}"
  total_size = 0
  for path in _chunk_paths(destination, spec.canonical, count):
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
  expected_names = {path.name for path in _chunk_paths(destination, spec.canonical, count)}
  for path in destination.glob(f"{spec.canonical}.chunk*"):
    if re.fullmatch(re.escape(spec.canonical) + r"\.chunk\d+of\d+", path.name) and path.name not in expected_names:
      return False, f"unexpected stale chunk for {spec.target}: {path.name}"
  return True, "ok"


def local_artifact_valid(destination: Path, spec: ModelSpec, onnx_hash: str, tg_ref: str) -> bool:
  metadata_path = _metadata_path(destination, spec.canonical)
  try:
    metadata = json.loads(metadata_path.read_text())
    if (metadata.get("schema"), metadata.get("target"), metadata.get("canonical"), metadata.get("onnx_sha256"),
        metadata.get("tinygrad_ref"), metadata.get("backend")) != \
       (1, spec.target, spec.canonical, onnx_hash, tg_ref, spec.backend):
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
    return valid and Path(get_manifest_path(str(destination / spec.canonical))).read_text().strip() == str(len(chunks))
  except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
    return False


def _remove_obsolete_chunks(destination: Path, spec: ModelSpec, expected: set[str]) -> None:
  for path in destination.glob(f"{spec.canonical}.chunk*"):
    if re.fullmatch(re.escape(spec.canonical) + r"\.chunk\d+of\d+", path.name) and path.name not in expected:
      path.unlink(missing_ok=True)


def _write_metadata(destination: Path, artifact: dict[str, Any], source: str) -> None:
  chunks = []
  for chunk in artifact["chunks"]:
    path = destination / chunk["name"]
    chunks.append({"name": path.name, "size": path.stat().st_size, "sha256": _hash_file(path)})
  metadata = {
    "schema": 1,
    "target": artifact["target"],
    "canonical": artifact["canonical"],
    "backend": artifact.get("backend", MODEL_SPECS[artifact["target"]].backend),
    "onnx_sha256": artifact["onnx_sha256"],
    "tinygrad_ref": artifact["tinygrad_ref"],
    "source": source,
    "chunks": chunks,
  }
  path = _metadata_path(destination, artifact["canonical"])
  temp = path.with_name(f".{path.name}.tmp")
  temp.write_text(json.dumps(metadata, sort_keys=True) + "\n")
  os.replace(temp, path)


def write_local_metadata(repo_root: Path, target: str) -> None:
  spec = MODEL_SPECS[target]
  destination = repo_root / "openpilot/selfdrive/modeld/models"
  onnx_hash = onnx_sha256(repo_root, spec.onnx)
  tg_ref = tinygrad_ref(repo_root)
  manifest = destination / get_manifest_path(str(destination / spec.canonical))
  count = int(manifest.read_text().strip())
  paths = _chunk_paths(destination, spec.canonical, count)
  _remove_obsolete_chunks(destination, spec, {path.name for path in paths})
  valid, detail = validate_artifact_files(destination, spec)
  if not valid:
    raise RuntimeError(detail)
  if not all(path.is_file() for path in paths):
    raise RuntimeError(f"incomplete {target} model chunks")
  artifact = {"target": target, "canonical": spec.canonical, "onnx_sha256": onnx_hash,
              "tinygrad_ref": tg_ref, "backend": spec.backend,
              "chunks": [{"name": path.name} for path in paths]}
  _write_metadata(destination, artifact, "local")


def _download_chunk(chunk: dict[str, Any], staging: Path, timeout: float) -> None:
  final = staging / chunk["name"]
  partial = final.with_suffix(final.suffix + ".part")
  request = Request(chunk["url"], headers={"User-Agent": "openpilot-model-fetcher"})
  digest = hashlib.sha256()
  size = 0
  with urlopen(request, timeout=timeout) as response, open(partial, "wb") as output:
    while block := response.read(1024 * 1024):
      size += len(block)
      if size > MAX_CHUNK_SIZE:
        raise ValueError(f"remote chunk is too large: {chunk['name']}")
      digest.update(block)
      output.write(block)
    output.flush()
    os.fsync(output.fileno())
  if digest.hexdigest() != chunk["sha256"]:
    raise ValueError(f"SHA-256 mismatch for {chunk['name']}")
  os.replace(partial, final)


def install_remote_artifact(destination: Path, artifact: dict[str, Any], timeout: float = CHUNK_TIMEOUT,
                            workers: int = 8) -> None:
  destination.mkdir(parents=True, exist_ok=True)
  staging = Path(tempfile.mkdtemp(prefix=f".{artifact['canonical']}.", dir=destination))
  try:
    with ThreadPoolExecutor(max_workers=min(workers, len(artifact["chunks"]))) as executor:
      futures = [executor.submit(_download_chunk, chunk, staging, timeout) for chunk in artifact["chunks"]]
      for future in as_completed(futures):
        future.result()

    count = len(artifact["chunks"])
    for chunk in artifact["chunks"]:
      os.replace(staging / chunk["name"], destination / chunk["name"])
    _write_metadata(destination, artifact, "huggingface")
    manifest = Path(get_manifest_path(str(destination / artifact["canonical"])))
    manifest_tmp = manifest.with_name(f".{manifest.name}.tmp")
    manifest_tmp.write_text(str(count) + "\n")
    os.replace(manifest_tmp, manifest)
    _remove_obsolete_chunks(destination, MODEL_SPECS[artifact["target"]],
                             {chunk["name"] for chunk in artifact["chunks"]})
  finally:
    for path in staging.glob("*"):
      path.unlink(missing_ok=True)
    staging.rmdir()


def fetch_target(repo_root: Path, target: str, destination: Path | None = None,
                 metadata_url: str | None = None) -> dict[str, Any]:
  spec = MODEL_SPECS[target]
  destination = destination or repo_root / "openpilot/selfdrive/modeld/models"
  try:
    onnx_hash = onnx_sha256(repo_root, spec.onnx)
    tg_ref = tinygrad_ref(repo_root)
  except (OSError, RuntimeError, ValueError) as e:
    return {"target": target, "status": "remote_unavailable", "error": str(e)}
  if local_artifact_valid(destination, spec, onnx_hash, tg_ref):
    return {"target": target, "status": "cache_hit", "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref}
  # A stale sidecar would otherwise make SCons consider the old chunk set
  # complete even when the identity or one of its hashes no longer matches.
  _metadata_path(destination, spec.canonical).unlink(missing_ok=True)
  try:
    artifact = resolve_remote(spec, onnx_hash, tg_ref, metadata_url=metadata_url)
  except (HTTPError, URLError, TimeoutError, OSError) as e:
    return {"target": target, "status": "remote_unavailable", "error": str(e),
            "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref}
  except (ValueError, json.JSONDecodeError, TypeError, KeyError) as e:
    return {"target": target, "status": "remote_invalid", "error": str(e),
            "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref}
  if artifact is None:
    return {"target": target, "status": "remote_miss", "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref}
  try:
    install_remote_artifact(destination, artifact)
  except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
    return {"target": target, "status": "remote_invalid", "error": str(e),
            "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref}
  return {"target": target, "status": "remote_hit", "onnx_sha256": onnx_hash, "tinygrad_ref": tg_ref}


def fetch_targets(repo_root: Path, targets: list[str], destination: Path | None = None,
                  metadata_url: str | None = None) -> dict[str, Any]:
  results = [fetch_target(repo_root, target, destination, metadata_url) for target in targets]
  return {"results": results, "skip": {target: result["status"] in ("cache_hit", "local_hit", "remote_hit")
                                        for target, result in ((r["target"], r) for r in results)}}


def validate_targets(destination: Path, targets: list[str]) -> dict[str, Any]:
  results = []
  for target in targets:
    spec = MODEL_SPECS[target]
    valid, detail = validate_artifact_files(destination, spec)
    results.append({"target": target, "valid": valid, "detail": detail})
  return {"results": results, "valid": all(result["valid"] for result in results)}


def validate_compatible_targets(repo_root: Path, destination: Path, targets: list[str]) -> dict[str, Any]:
  results = []
  for target in targets:
    spec = MODEL_SPECS[target]
    try:
      onnx_hash = onnx_sha256(repo_root, spec.onnx)
      tg_ref = tinygrad_ref(repo_root)
      valid = local_artifact_valid(destination, spec, onnx_hash, tg_ref)
      detail = "ok" if valid else f"incompatible or invalid {target} artifact"
    except (OSError, RuntimeError, ValueError) as e:
      valid, detail = False, str(e)
    results.append({"target": target, "valid": valid, "detail": detail})
  return {"results": results, "valid": all(result["valid"] for result in results)}


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--repo-root", default=".")
  parser.add_argument("--targets", nargs="+", choices=sorted(MODEL_SPECS), default=["small", "dm"])
  parser.add_argument("--destination")
  parser.add_argument("--validate", action="store_true")
  parser.add_argument("--compatible", action="store_true", help="also verify local artifact identity")
  parser.add_argument("--metadata-url")
  args = parser.parse_args(argv)
  repo_root = Path(args.repo_root).resolve()
  destination = Path(args.destination).resolve() if args.destination else repo_root / "openpilot/selfdrive/modeld/models"
  if args.validate:
    result = validate_compatible_targets(repo_root, destination, args.targets) if args.compatible else validate_targets(destination, args.targets)
  else:
    result = fetch_targets(repo_root, args.targets, destination=destination, metadata_url=args.metadata_url)
  print(json.dumps(result, sort_keys=True))
  return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
  raise SystemExit(main())
