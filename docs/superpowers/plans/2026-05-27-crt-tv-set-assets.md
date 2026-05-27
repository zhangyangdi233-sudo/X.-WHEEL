# CRT TV Set Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CRT TV asset and a single Blender-importable integrated GLB set using the shared green/pale/deep-blue palette.

**Architecture:** Extend `tools/create_psx_dvr_assets.py` with palette constants, CRT geometry, transformed asset composition, combined GLB export, and manifest/report checks. Add `tools/test_psx_dvr_assets.py` as standard-library tests for the generator outputs and GLB structure.

**Tech Stack:** Python 3 standard library, glTF 2.0 binary `.glb`, generated PNG textures, existing software preview renderer.

---

## File Structure

- Modify `tools/create_psx_dvr_assets.py`: add palette constants, CRT builder, combined set builder/export, report checks, and manifest entries.
- Create `tools/test_psx_dvr_assets.py`: test generated assets, metadata, budgets, palette entries, and combined set composition.
- Create `assets/3d/crt_tv/crt_tv.glb`: independent CRT asset.
- Create `assets/3d/crt_tv/crt_tv_texture.png`: CRT texture.
- Create `assets/3d/crt_tv/crt_tv_preview.png`: CRT preview.
- Create `assets/3d/psx_dvr_crt_set/psx_dvr_crt_set.glb`: Blender-importable combined set.
- Create `assets/3d/psx_dvr_crt_set/psx_dvr_crt_set_texture.png`: generated embedded texture source for the combined set GLB.
- Create `assets/3d/psx_dvr_crt_set/psx_dvr_crt_set_preview.png`: combined set preview.
- Modify `assets/3d/psx_dvr_assets_manifest.json`: add CRT and combined set metadata.

## Task 1: Failing Verification

- [ ] **Step 1: Add tests**

Create `tools/test_psx_dvr_assets.py` with `unittest` tests that run the generator, load the manifest, and assert:

```python
self.assertIn("crt_tv", assets)
self.assertIn("psx_dvr_crt_set", assets)
self.assertEqual(assets["crt_tv"]["texture_size"], [256, 256])
self.assertGreaterEqual(assets["crt_tv"]["triangles"], 900)
self.assertLessEqual(assets["crt_tv"]["triangles"], 1800)
self.assertEqual(assets["psx_dvr_crt_set"]["blender_import"], "Import GLB in Blender")
self.assertEqual(manifest["palette"]["primary"], ["#3FA943", "#E8F8E4", "#0C1725"])
```

- [ ] **Step 2: Verify tests fail before implementation**

Run: `python -m unittest tools.test_psx_dvr_assets -v`

Expected: fails because `crt_tv`, `psx_dvr_crt_set`, and `palette` are not in the manifest yet.

## Task 2: Generator Extension

- [ ] **Step 1: Add production code**

Modify `tools/create_psx_dvr_assets.py` to:

- Define `PALETTE = {"green": "#3FA943", "pale": "#E8F8E4", "deep": "#0C1725"}` and RGB helpers.
- Recolor existing console/disc materials toward the palette.
- Add `build_crt_tv_asset()`.
- Add transform helpers and `build_integrated_set_asset(console, disc, crt)`.
- Generate `crt_tv` and `psx_dvr_crt_set` in `generate_assets()`.
- Include `palette` and `blender_import` metadata in the manifest.
- Extend `verify_outputs()` and `report_outputs()` to include CRT and set assets.

- [ ] **Step 2: Run generator**

Run: `python tools/create_psx_dvr_assets.py`

Expected: prints console, disc, CRT, and set triangle/material counts.

## Task 3: Verification

- [ ] **Step 1: Run tests**

Run: `python -m unittest tools.test_psx_dvr_assets -v`

Expected: all tests pass.

- [ ] **Step 2: Run generator checks**

Run:

```powershell
python -m py_compile tools/create_psx_dvr_assets.py tools/test_psx_dvr_assets.py
python tools/create_psx_dvr_assets.py --verify
python tools/create_psx_dvr_assets.py --report
python tools/validate_cartridge_overhaul.py
```

Expected: all commands exit 0.

## Self-Review

- Spec coverage: CRT asset, integrated Blender-importable GLB, palette update, manifest, previews, and validation are covered.
- Red-flag scan: no incomplete-work markers remain.
- Type consistency: paths and asset keys match the design spec.
