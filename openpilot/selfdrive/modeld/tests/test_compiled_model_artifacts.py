import json
from pathlib import Path

from openpilot.common.file_chunker import get_manifest_path
from openpilot.selfdrive.modeld import compiled_model_artifacts as artifacts


def _write_artifact(destination: Path, spec: artifacts.ModelSpec, data: bytes = b"model chunk") -> Path:
  destination.mkdir(parents=True)
  chunk = destination / f"{spec.canonical}.chunk01of01"
  chunk.write_bytes(data)
  Path(get_manifest_path(str(destination / spec.canonical))).write_text("1\n")
  return chunk


def test_local_artifact_validation_checks_manifest_chunks_and_hashes(monkeypatch, tmp_path: Path):
  spec = artifacts.MODEL_SPECS["small"]
  destination = tmp_path / "openpilot/selfdrive/modeld/models"
  chunk = _write_artifact(destination, spec)
  monkeypatch.setattr(artifacts, "onnx_sha256", lambda repo_root, relative_path: "a" * 64)
  monkeypatch.setattr(artifacts, "tinygrad_ref", lambda repo_root: "b" * 40)

  artifacts.write_local_metadata(tmp_path, "small")

  assert artifacts.local_artifact_valid(destination, spec, "a" * 64, "b" * 40, required_source="local")
  chunk.write_bytes(b"corrupt")
  assert not artifacts.local_artifact_valid(destination, spec, "a" * 64, "b" * 40, required_source="local")


def test_write_local_metadata_records_identity_and_origin(monkeypatch, tmp_path: Path):
  spec = artifacts.MODEL_SPECS["big"]
  destination = tmp_path / "openpilot/selfdrive/modeld/models"
  _write_artifact(destination, spec, b"locally compiled big model")
  monkeypatch.setattr(artifacts, "onnx_sha256", lambda repo_root, relative_path: "a" * 64)
  monkeypatch.setattr(artifacts, "tinygrad_ref", lambda repo_root: "b" * 40)

  artifacts.write_local_metadata(tmp_path, "big")

  metadata = json.loads((destination / f"{spec.canonical}.metadata.json").read_text())
  assert metadata["source"] == "local"
  assert metadata["onnx_sha256"] == "a" * 64
  assert metadata["tinygrad_ref"] == "b" * 40


def test_validation_rejects_non_local_artifact_metadata(monkeypatch, tmp_path: Path):
  spec = artifacts.MODEL_SPECS["small"]
  destination = tmp_path / "openpilot/selfdrive/modeld/models"
  _write_artifact(destination, spec)
  monkeypatch.setattr(artifacts, "onnx_sha256", lambda repo_root, relative_path: "a" * 64)
  monkeypatch.setattr(artifacts, "tinygrad_ref", lambda repo_root: "b" * 40)
  artifacts.write_local_metadata(tmp_path, "small")
  metadata_path = destination / f"{spec.canonical}.metadata.json"
  metadata = json.loads(metadata_path.read_text())
  metadata["source"] = "huggingface"
  metadata_path.write_text(json.dumps(metadata))

  result = artifacts.validate_compatible_targets(tmp_path, destination, ["small"], required_source="local")

  assert not result["valid"]
  assert "non-local" in result["results"][0]["detail"]


def test_packaged_validation_verifies_recorded_chunk_hash(monkeypatch, tmp_path: Path):
  spec = artifacts.MODEL_SPECS["dm"]
  destination = tmp_path / "openpilot/selfdrive/modeld/models"
  chunk = _write_artifact(destination, spec)
  monkeypatch.setattr(artifacts, "onnx_sha256", lambda repo_root, relative_path: "a" * 64)
  monkeypatch.setattr(artifacts, "tinygrad_ref", lambda repo_root: "b" * 40)
  artifacts.write_local_metadata(tmp_path, "dm")
  chunk.write_bytes(b"same-size!!")

  result = artifacts.validate_targets(destination, ["dm"], required_source="local")

  assert not result["valid"]


def test_cli_rejects_fetch_mode():
  try:
    artifacts.main([])
  except SystemExit as e:
    assert e.code == 2
  else:
    raise AssertionError("validation flag should be mandatory")
