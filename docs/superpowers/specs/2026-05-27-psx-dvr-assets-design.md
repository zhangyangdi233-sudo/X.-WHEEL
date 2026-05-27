# PSX DVR-Style Console Assets Design

## Goal

Create two separate, game-ready low-poly 3D assets for the Godot project: a logo-free PSX DVR-inspired console body and a matching optical game disc. The assets should evoke a 2003 Japanese living-room electronics device with PlayStation-era game hardware DNA, without reproducing protected branding.

## Asset Brief

### Console

- Type: hero prop / diegetic object.
- Gameplay purpose: a readable interactable console prop for menu, cartridge/disc selection, or scene dressing.
- World size: about 3.1 units wide, 3.2 units deep, 0.85 units tall.
- Camera distance: close-to-mid shot, readable from 3-6 units away.
- Triangle budget: 900-1,800 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus simple flat materials.
- Rigging: none.
- Collision: simple box collision proxy.
- Export: `glb`, with Blender source and preview image.

### Disc

- Type: small hand prop / media object.
- Gameplay purpose: the era-correct replacement for the earlier cartridge idea.
- World size: about 0.95 units diameter, thin enough to read clearly as a disc.
- Camera distance: close shot or placed beside the console.
- Triangle budget: 200-700 triangles.
- Texture budget: one 128x128 nearest-filter texture atlas plus flat materials.
- Rigging: none.
- Collision: simple cylinder/disc collision proxy.
- Export: `glb`, with Blender source and preview image.

## Visual Direction

The console uses a compact white DVR appliance silhouette: rectangular body, slight top step, front optical tray seam, controller ports, memory card slots, USB/Memory Stick-like front details, small red/green status lights, and hard-edged plastic bevels. Materials should read as aged warm-white plastic, black recessed ports, muted red/green indicator lights, and gray rubber feet.

The disc uses a simplified DVD/game-disc form: low-sided circular mesh, center hole, silver reflective face suggested through flat color bands, and a small low-resolution printed label area. It should look like a physical disc made for the console, not a cartridge.

## Style Rules

- Low-poly, flat shaded, hard normals.
- No Sony, PlayStation, PSX, PS2, DVD, or other real logos.
- Use short fictional markings such as `XW-03`, `HDD+GAME`, and small abstract icons.
- Texture details should be pixel-painted: panel lines, port shadows, tiny warning ticks, and light wear.
- Preserve PSX/PS1 game-asset flavor through visible triangles, low-resolution textures, and limited palette rather than modern realism.

## Output Paths

- `assets/3d/psx_dvr_console/psx_dvr_console.glb`
- `assets/3d/psx_dvr_console/psx_dvr_console_texture.png`
- `assets/3d/psx_dvr_console/psx_dvr_console_preview.png`
- `assets/3d/psx_dvr_disc/psx_dvr_disc.glb`
- `assets/3d/psx_dvr_disc/psx_dvr_disc_texture.png`
- `assets/3d/psx_dvr_disc/psx_dvr_disc_preview.png`
- `assets/3d/psx_dvr_assets_manifest.json`
- `assets/3d/psx_dvr_assets.blend`
- `assets/3d/psx_dvr_blender_import_report.json`
- `tools/create_psx_dvr_assets.py`
- `tools/verify_psx_dvr_single_assets.py`

Each exported GLB must import into Blender as exactly one mesh object. The generated `.blend` scene must therefore contain exactly two mesh objects: `psx_dvr_console` and `psx_dvr_disc`.

## Verification

- Validate exported GLB files with the generator's `--verify` mode.
- Validate single-asset structure with `tools/verify_psx_dvr_single_assets.py`.
- Confirm object origins are centered and transforms are applied.
- Confirm each asset is separate and has stable ASCII object/material names.
- Record triangle counts, material counts, and texture sizes.
- Save one preview render per asset.
