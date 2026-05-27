"""Verify PSX DVR exports are two usable assets, not many loose parts."""

from __future__ import annotations

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "assets" / "3d"


def read_glb_json(path: Path) -> dict:
    data = path.read_bytes()
    if data[:4] != b"glTF":
        raise AssertionError(f"{path}: invalid GLB magic")
    json_length, json_type = struct.unpack_from("<I4s", data, 12)
    if json_type != b"JSON":
        raise AssertionError(f"{path}: missing JSON chunk")
    return json.loads(data[20 : 20 + json_length].decode("utf-8"))


def assert_single_asset(path: Path, expected_name: str) -> None:
    document = read_glb_json(path)
    meshes = document.get("meshes", [])
    nodes = document.get("nodes", [])
    scenes = document.get("scenes", [])

    if len(meshes) != 1:
        raise AssertionError(f"{expected_name}: expected 1 mesh, got {len(meshes)}")
    if len(nodes) != 1:
        raise AssertionError(f"{expected_name}: expected 1 node, got {len(nodes)}")
    if meshes[0].get("name") != expected_name:
        raise AssertionError(f"{expected_name}: mesh name mismatch: {meshes[0].get('name')}")
    if nodes[0].get("name") != expected_name:
        raise AssertionError(f"{expected_name}: node name mismatch: {nodes[0].get('name')}")
    if scenes and scenes[0].get("nodes") != [0]:
        raise AssertionError(f"{expected_name}: scene should reference only node 0")


def main() -> None:
    assert_single_asset(ASSET_ROOT / "psx_dvr_console" / "psx_dvr_console.glb", "psx_dvr_console")
    assert_single_asset(ASSET_ROOT / "psx_dvr_disc" / "psx_dvr_disc.glb", "psx_dvr_disc")
    print("single asset GLB verification passed")


if __name__ == "__main__":
    main()
