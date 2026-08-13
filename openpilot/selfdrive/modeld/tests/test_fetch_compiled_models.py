import hashlib
import io
from pathlib import Path

import pytest

from openpilot.common.file_chunker import get_manifest_path
from openpilot.selfdrive.modeld import fetch_compiled_models as fetcher


def _metadata(spec: fetcher.ModelSpec, onnx_hash: str, tg_ref: str, chunks: list[tuple[str, bytes]]) -> dict:
  return {
    "tinygrad_ref": tg_ref,
    "bundles": [{
      "onnx_sha256": onnx_hash,
      "models": [{
        "type": "chunked",
        "artifact": {
          "file_name": spec.canonical,
          "chunks": [{
            "file_name": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "url": f"https://example.test/{name}",
          } for name, data in chunks],
        },
      }],
    }],
  }


def test_resolve_requires_exact_tinygrad_and_onnx():
  spec = fetcher.MODEL_SPECS["big"]
  chunks = [("remote.chunk01of01", b"model")]
  metadata = _metadata(spec, "a" * 64, "b" * 40, chunks)

  artifact = fetcher._artifact_from_metadata(metadata, spec, "a" * 64, "b" * 40)
  assert artifact is not None
  assert artifact["chunks"][0]["name"] == "big_driving_tinygrad.pkl.chunk01of01"
  assert fetcher._artifact_from_metadata(metadata, spec, "a" * 64, "c" * 40) is None
  assert fetcher._artifact_from_metadata(metadata, spec, "d" * 64, "b" * 40) is None


def test_resolve_rejects_unsafe_chunk_name():
  spec = fetcher.MODEL_SPECS["small"]
  metadata = _metadata(spec, "a" * 64, "b" * 40, [("../chunk01of01", b"model")])
  with pytest.raises(ValueError, match="unsafe model chunk filename"):
    fetcher._artifact_from_metadata(metadata, spec, "a" * 64, "b" * 40)


def test_local_artifact_validation_checks_manifest_chunks_and_hashes(tmp_path: Path):
  spec = fetcher.MODEL_SPECS["small"]
  destination = tmp_path / "models"
  destination.mkdir()
  data = b"model chunk"
  chunk = destination / f"{spec.canonical}.chunk01of01"
  chunk.write_bytes(data)
  manifest = Path(get_manifest_path(str(destination / spec.canonical)))
  manifest.write_text("1\n")
  artifact = {
    "target": spec.target,
    "canonical": spec.canonical,
    "onnx_sha256": "a" * 64,
    "tinygrad_ref": "b" * 40,
    "chunks": [{"name": chunk.name}],
  }
  fetcher._write_metadata(destination, artifact, "local")

  assert fetcher.local_artifact_valid(destination, spec, "a" * 64, "b" * 40)
  chunk.write_bytes(b"corrupt")
  assert not fetcher.local_artifact_valid(destination, spec, "a" * 64, "b" * 40)


def test_remote_install_writes_manifest_last(monkeypatch, tmp_path: Path):
  spec = fetcher.MODEL_SPECS["small"]
  data = b"downloaded"
  artifact = {
    "target": spec.target,
    "canonical": spec.canonical,
    "onnx_sha256": "a" * 64,
    "tinygrad_ref": "b" * 40,
    "chunks": [{
      "index": 1,
      "url": "https://example.test/chunk",
      "sha256": hashlib.sha256(data).hexdigest(),
      "name": f"{spec.canonical}.chunk01of01",
    }],
  }

  class Response(io.BytesIO):
    def __enter__(self):
      return self

    def __exit__(self, *args):
      self.close()

  monkeypatch.setattr(fetcher, "urlopen", lambda request, timeout: Response(data))
  destination = tmp_path / "models"
  fetcher.install_remote_artifact(destination, artifact, workers=1)

  assert (destination / artifact["chunks"][0]["name"]).read_bytes() == data
  assert Path(get_manifest_path(str(destination / spec.canonical))).read_text() == "1\n"
  assert fetcher.local_artifact_valid(destination, spec, "a" * 64, "b" * 40)
