import hashlib
import json

import pytest
from scripts import acquire_phase1
from scripts.build_geography import Terrain, dms


def test_corrupt_cache_is_not_silently_reused(tmp_path, monkeypatch):
    monkeypatch.setattr(acquire_phase1, "RAW", tmp_path)
    (tmp_path / "sample.json").write_text("corrupted")
    (tmp_path / "sample.json.metadata.json").write_text(json.dumps({"sha256": hashlib.sha256(b"original").hexdigest()}))
    with pytest.raises(ValueError, match="checksum mismatch"):
        acquire_phase1.fetch("sample.json", "https://example.invalid/not-called")


def test_malformed_document_coordinates_are_rejected():
    assert dms([27, 30, 0]) == 27.5
    with pytest.raises(ValueError):
        dms([27, 35, 354])


def test_terrain_seam_and_outside_coverage():
    terrain = Terrain()
    try:
        for lon in (93.9996, 94.0, 94.0004):
            elevation, slope = terrain.sample(lon, 27.0756)
            assert elevation is not None and 0 <= slope < 90
        assert terrain.sample(0, 0) == (None, None)
    finally:
        terrain.close()
