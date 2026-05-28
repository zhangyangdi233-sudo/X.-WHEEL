# CRT TV Room Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Revise the CRT into a large-bezel box TV with convex black glass, remove the integrated set asset, and add separate bookshelf, desk, player-sittable beanbag chair, and disc rug assets using the shared green/pale/deep-blue palette.

**Architecture:** Update `tools/create_psx_dvr_assets.py` with large-bezel CRT geometry, convex black glass materials, bookshelf/desk/beanbag/rug geometry, asset size metadata, and manifest/report checks. Update `tools/test_psx_dvr_assets.py` to enforce no integrated set, new assets, CRT reference metadata, single-body beanbag metadata, disc rug metadata, and relative size ordering.

**Tech Stack:** Python 3 standard library, glTF 2.0 binary `.glb`, generated PNG textures, existing software preview renderer.

---

## File Structure

- Modify `tools/create_psx_dvr_assets.py`: remove integrated set generation, revise CRT screen/front geometry, add bookshelf, desk, beanbag, and disc rug builders, add size metadata/report checks.
- Modify `tools/test_psx_dvr_assets.py`: test generated assets, metadata, budgets, palette entries, absence of set, dark CRT screen, single-body beanbag metadata, disc rug metadata, and size ordering.
- Modify `tools/blender_mcp/install_and_import_psx_dvr_assets.py`: import individual console, disc, CRT, bookshelf, desk, beanbag, and disc rug assets only.
- Modify `assets/3d/crt_tv/crt_tv.glb`, texture, and preview.
- Create `assets/3d/bookshelf/bookshelf.glb`, texture, and preview.
- Create `assets/3d/desk/desk.glb`, texture, and preview.
- Create `assets/3d/beanbag_chair/beanbag_chair.glb`, texture, and preview.
- Create `assets/3d/disc_rug/disc_rug.glb`, texture, and preview.
- Delete individual `assets/3d/psx_dvr_crt_set/*` files.
- Modify `assets/3d/psx_dvr_assets_manifest.json`, `.blend`, and Blender import report.

## Task 1: Failing Verification

- [ ] **Step 1: Add tests**

Update `tools/test_psx_dvr_assets.py` with `unittest` tests that run the generator, load the manifest, and assert:

```python
self.assertIn("crt_tv", assets)
self.assertIn("bookshelf", assets)
self.assertIn("desk", assets)
self.assertNotIn("psx_dvr_crt_set", assets)
self.assertEqual(assets["crt_tv"]["texture_size"], [256, 256])
self.assertEqual(assets["crt_tv"]["screen_state"], "black_glass")
self.assertEqual(assets["crt_tv"]["front_style"], "large_bezel_box_crt")
self.assertEqual(assets["crt_tv"]["screen_material"], "convex_black_glass")
self.assertEqual(assets["crt_tv"]["control_layout"], "bottom_button_row")
self.assertIn("beanbag_chair", assets)
self.assertEqual(assets["beanbag_chair"]["seat_role"], "player_sittable")
self.assertEqual(assets["beanbag_chair"]["shape_construction"], "single_sculpted_body")
self.assertEqual(assets["beanbag_chair"]["fabric_style"], "sculpted_green_velour")
self.assertIn("disc_rug", assets)
self.assertEqual(assets["disc_rug"]["surface_role"], "floor_rug")
self.assertEqual(assets["disc_rug"]["rug_style"], "green_disc_rug")
self.assertGreater(assets["bookshelf"]["dimensions"][2], assets["crt_tv"]["dimensions"][2])
self.assertGreater(assets["desk"]["dimensions"][0], assets["crt_tv"]["dimensions"][0])
self.assertGreater(assets["crt_tv"]["dimensions"][0], assets["psx_dvr_console"]["dimensions"][0] * 0.6)
self.assertEqual(manifest["palette"]["primary"], ["#3FA943", "#E8F8E4", "#0C1725"])
```

- [ ] **Step 2: Verify tests fail before implementation**

Run: `python -m unittest tools.test_psx_dvr_assets -v`

Expected: fails because current output lacks large-bezel CRT metadata, single-body beanbag metadata, or `disc_rug`.

## Task 2: Generator Extension

- [ ] **Step 1: Add production code**

Modify `tools/create_psx_dvr_assets.py` to:

- Change CRT geometry, screen materials, and texture to a large-bezel box CRT with convex black glass and subtle green/pale reflections.
- Remove `build_integrated_set_asset()` and omit `psx_dvr_crt_set` from generation, verification, report, and manifest.
- Add `build_bookshelf_asset()`, `build_desk_asset()`, `build_beanbag_asset()`, and `build_disc_rug_asset()`.
- Include `dimensions`, `screen_state`, and palette metadata in the manifest.
- Extend `verify_outputs()` and `report_outputs()` to include console, disc, CRT, bookshelf, desk, beanbag, and disc rug only.

- [ ] **Step 2: Run generator**

Run: `python tools/create_psx_dvr_assets.py`

Expected: prints console, disc, CRT, bookshelf, desk, beanbag, and disc rug triangle/material counts.

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

- Spec coverage: large-bezel black-glass CRT, no integrated set, bookshelf, desk, single-body beanbag, disc rug, size ordering, palette, manifest, previews, Blender scene, and validation are covered.
- Red-flag scan: no incomplete-work markers remain.
- Type consistency: paths and asset keys match the design spec.
