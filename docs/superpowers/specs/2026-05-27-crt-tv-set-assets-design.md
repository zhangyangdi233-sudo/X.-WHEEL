# CRT TV, Furniture, and Disc Rug Assets Design

## Goal

Create separate low-poly room props that match the existing PSX DVR-style console and disc assets: CRT television, bookshelf, desk, player-sittable beanbag chair, and disc-style floor rug. Each object must be an individual GLB asset and an individual asset in the generated Blender scene.

## Palette

Use these three colors as the primary palette, with small value shifts for readability:

- `#3FA943`: green accent, power lights, labels, and small screen reflections.
- `#E8F8E4`: pale plastic highlights, book pages, and small reflective highlights.
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

## CRT Screen Revision

The CRT screen should read as inactive convex black glass, not an active pale green display. The front silhouette should be a large-bezel box CRT like the reference: deep case, dominant recessed glass, bottom row of small controls, no right-side control panel. Use deep blue-black glass with subtle green/pale reflections and low-resolution scanline marks. The screen remains suitable for in-game content or CRT post-processing to appear on top later.

## Bookshelf Asset Brief

- Type: room prop / environmental furniture.
- Gameplay purpose: readable background prop near the TV setup.
- World size: larger than the CRT, about 2.9 units wide, 0.55 units deep, 2.4 units tall.
- Triangle budget: 900-1,800 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Desk Asset Brief

- Type: room prop / environmental furniture.
- Gameplay purpose: support prop for the console/TV setup or room dressing.
- World size: larger than the CRT, about 3.4 units wide, 1.65 units deep, 1.05 units tall.
- Triangle budget: 900-1,800 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Beanbag Chair Asset Brief

- Type: interactable room prop / player-sittable furniture.
- Gameplay purpose: a lazy sofa seat the player character can sit in near the CRT setup.
- World size: about 2.3 units wide, 2.0 units deep, 1.1 units tall.
- Triangle budget: 900-2,200 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Material read: sculpted green velour/fabric with soft radial folds and a small side tag.
- Construction: one sculpted cushion body mesh with a central sink; avoid blocky separate arm/back cushion construction.
- Collision: simple sit-volume collision proxy.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Disc Rug Asset Brief

- Type: floor prop / environmental dressing.
- Gameplay purpose: readable circular rug for the player room, visually tying the disc/console theme into the floor layout.
- World size: about 3.4 units wide, 3.4 units deep, 0.05 units tall.
- Triangle budget: 250-1,200 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Visual reference: green translucent record/game-disc rug with original X WHEEL labels, not copied brand/IP text.
- Collision: thin floor box collision proxy.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Scale Rule

Generated asset metadata must enforce this relative size ordering:

- `bookshelf` and `desk` are both larger than `crt_tv`.
- `crt_tv` is larger than `psx_dvr_console`.
- `beanbag_chair` is wide and deep enough to read as player-sittable room furniture.
- `disc_rug` is wider than the beanbag and remains a thin floor asset.
- `psx_dvr_disc` remains a small separate prop.

## Visual Direction

The CRT uses a chunky early-2000s desktop TV silhouette: deep blue-black shell, large thick bezel, dominant inset convex black glass screen, bottom button row, small green power light, rear tube bulge, vents, and small feet. Geometry should stay hard-edged and visibly low-poly.

The bookshelf and desk should use the same restricted palette: deep casing/shadows, pale highlights, and green labels or worn paint accents. They should feel like part of the same PSX-era room rather than realistic furniture.

The beanbag chair uses a rounded low-poly sculpted cushion silhouette with a depressed center and radial fabric folds. It should read as one soft object, not a furniture assembly.

The disc rug uses a flat circular mat, dark rim, center label, green swirl fields, and original non-branded markings inspired by game discs and colored vinyl.

## Output Paths

- `assets/3d/crt_tv/crt_tv.glb`
- `assets/3d/crt_tv/crt_tv_texture.png`
- `assets/3d/crt_tv/crt_tv_preview.png`
- `assets/3d/bookshelf/bookshelf.glb`
- `assets/3d/bookshelf/bookshelf_texture.png`
- `assets/3d/bookshelf/bookshelf_preview.png`
- `assets/3d/desk/desk.glb`
- `assets/3d/desk/desk_texture.png`
- `assets/3d/desk/desk_preview.png`
- `assets/3d/beanbag_chair/beanbag_chair.glb`
- `assets/3d/beanbag_chair/beanbag_chair_texture.png`
- `assets/3d/beanbag_chair/beanbag_chair_preview.png`
- `assets/3d/disc_rug/disc_rug.glb`
- `assets/3d/disc_rug/disc_rug_texture.png`
- `assets/3d/disc_rug/disc_rug_preview.png`
- `assets/3d/psx_dvr_assets_manifest.json`
- `assets/3d/psx_dvr_assets.blend`
- `assets/3d/psx_dvr_blender_import_report.json`
- `tools/create_psx_dvr_assets.py`
- `tools/test_psx_dvr_assets.py`

## Verification

- Run generator syntax checks.
- Run tests that fail before large-bezel CRT/single-body beanbag/disc-rug support exists and pass after implementation.
- Validate every generated GLB with the generator's `--verify` mode.
- Confirm `--report` enforces budgets, palette metadata, absence of `psx_dvr_crt_set`, CRT black-glass metadata, beanbag sit metadata, disc rug metadata, and relative size ordering.
- Visually inspect preview PNGs for non-empty, correctly framed assets.
- Regenerate the Blender scene and confirm it contains only individual assets: `psx_dvr_console`, `psx_dvr_disc`, `crt_tv`, `bookshelf`, `desk`, `beanbag_chair`, and `disc_rug`.
