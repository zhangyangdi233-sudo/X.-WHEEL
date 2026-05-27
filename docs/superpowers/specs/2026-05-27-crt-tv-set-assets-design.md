# CRT TV and Integrated Set Assets Design

## Goal

Create a low-poly CRT television asset that matches the existing PSX DVR-style console and disc assets, then export a single integrated GLB scene asset that can be imported into Blender as one arranged set.

## Palette

Use these three colors as the primary palette, with small value shifts for readability:

- `#3FA943`: green accent, screen glow, power light, small labels.
- `#E8F8E4`: pale phosphor screen and light plastic highlights.
- `#0C1725`: deep blue-black casing, recesses, shadows, and ports.

The previous console and disc should also be recolored toward this palette when regenerated, so all assets read as one coherent set.

## CRT TV Asset Brief

- Type: hero prop / diegetic object.
- Gameplay purpose: readable CRT prop for menu scenes, room dressing, or monitor display.
- World size: about 2.2 units wide, 1.7 units deep, 1.65 units tall.
- Camera distance: close-to-mid shot, readable from 3-6 units away.
- Triangle budget: 900-1,800 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus simple flat materials.
- Rigging: none.
- Collision: simple box collision proxy.
- Export: GLB, texture PNG, preview PNG, and manifest metadata.

## Integrated Set Brief

Export one Blender-compatible GLB scene asset containing:

- `psx_dvr_console`
- `psx_dvr_disc`
- `crt_tv`

The set should place the CRT behind the console, with the disc offset near the front. This integrated asset is intended for Blender import and scene dressing. Blender is not available in the local environment, so the deliverable is a GLB file that Blender can import, not a native `.blend` file.

## Visual Direction

The CRT uses a chunky early-2000s desktop TV silhouette: deep blue-black shell, slightly inset pale green convex screen, right-side control panel, low-poly knobs, speaker holes, small green power light, rear tube bulge, vents, and small feet. Geometry should stay hard-edged and visibly low-poly.

The integrated set should preserve separate object names and stable ASCII material names so Blender users can select or edit individual pieces after importing.

## Output Paths

- `assets/3d/crt_tv/crt_tv.glb`
- `assets/3d/crt_tv/crt_tv_texture.png`
- `assets/3d/crt_tv/crt_tv_preview.png`
- `assets/3d/psx_dvr_crt_set/psx_dvr_crt_set.glb`
- `assets/3d/psx_dvr_crt_set/psx_dvr_crt_set_preview.png`
- `assets/3d/psx_dvr_assets_manifest.json`
- `tools/create_psx_dvr_assets.py`
- `tools/test_psx_dvr_assets.py`

## Verification

- Run generator syntax checks.
- Run tests that fail before CRT/set support exists and pass after implementation.
- Validate every generated GLB with the generator's `--verify` mode.
- Confirm `--report` enforces budgets and palette metadata.
- Visually inspect preview PNGs for non-empty, correctly framed assets.
