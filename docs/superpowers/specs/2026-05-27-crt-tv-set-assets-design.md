# CRT TV, Furniture, and Disc Rug Assets Design

## Goal

Create separate higher-detail low-poly room props that match the existing PSX DVR-style console and disc assets: CRT television, bookshelf, desk, player-sittable beanbag chair, and disc-style floor rug. Also create a composed `emi_room` scene asset that places these props into Emi's room layout, plus reusable individual clutter assets for posters, paper, lamp, stationery, plant, chair, books, and CD cases. Each object must be an individual GLB asset and an individual asset in the generated Blender scene.

## Palette

Use these three colors as the primary palette, with small value shifts for readability:

- `#3FA943`: green accent, power lights, labels, and small screen reflections.
- `#E8F8E4`: pale plastic highlights, book pages, and small reflective highlights.
- `#0C1725`: deep blue-black casing, recesses, shadows, and ports.

The previous console and disc should also be recolored toward this palette when regenerated, so all assets read as one coherent set.

## Scale And Detail

Use a five-head chibi character reference, about 1.40m tall. Desk height targets about 0.72m, CRT and console are tabletop props, and seats/rugs are sized for direct player interaction. Preserve the current green/pale/deep palette while increasing geometry density and small pixel-plane detail in the spirit of clean low-poly food/toy dioramas.

## CRT TV Asset Brief

- Type: hero prop / diegetic object.
- Gameplay purpose: readable CRT prop for menu scenes, room dressing, or monitor display.
- World size: about 0.70 units wide, 0.58 units deep, 0.56 units tall.
- Camera distance: close-to-mid shot, readable from 3-6 units away.
- Triangle budget: 2,200-5,200 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus simple flat materials.
- Rigging: none.
- Collision: simple box collision proxy.
- Export: GLB, texture PNG, preview PNG, and manifest metadata.

## CRT Screen Revision

The CRT screen should read as inactive convex black glass, not an active pale green display. The front silhouette should be a large-bezel box CRT like the reference: deep case, dominant recessed glass, bottom row of small controls, no right-side control panel. Use deep blue-black glass with subtle green/pale reflections and low-resolution scanline marks. The screen remains suitable for in-game content or CRT post-processing to appear on top later.

## Bookshelf Asset Brief

- Type: room prop / environmental furniture.
- Gameplay purpose: readable background prop near the TV setup.
- World size: larger than the CRT, about 1.20 units wide, 0.36 units deep, 1.55 units tall.
- Triangle budget: 1,800-5,200 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Desk Asset Brief

- Type: room prop / environmental furniture.
- Gameplay purpose: support prop for the console/TV setup or room dressing.
- World size: larger than the CRT, about 1.65 units wide, 0.82 units deep, 0.72 units tall.
- Triangle budget: 1,800-5,200 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Beanbag Chair Asset Brief

- Type: interactable room prop / player-sittable furniture.
- Gameplay purpose: a lazy sofa seat the player character can sit in near the CRT setup.
- World size: about 1.10 units wide, 1.00 units deep, 0.58 units tall.
- Triangle budget: 2,200-5,600 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Material read: sculpted green velour/fabric with soft radial folds and a small side tag.
- Construction: start from a UV-sphere style latitude/longitude mesh, then sculpt it into a flattened lazy-sofa form by compressing the bottom, sinking the center, puffing the rim, and adding radial folds. Avoid blocky separate arm/back cushion construction.
- Collision: simple sit-volume collision proxy.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Disc Rug Asset Brief

- Type: floor prop / environmental dressing.
- Gameplay purpose: readable circular rug for the player room, visually tying the disc/console theme into the floor layout.
- World size: about 1.70 units wide, 1.70 units deep, 0.035 units tall.
- Triangle budget: 1,200-3,200 triangles.
- Texture budget: one 256x256 nearest-filter texture atlas plus flat materials.
- Visual reference: green translucent record/game-disc rug with original X WHEEL labels, not copied brand/IP text.
- Collision: thin floor box collision proxy.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Emi Room Scene Asset Brief

- Type: composed character room environment asset.
- Gameplay purpose: room-scale set dressing for Emi's CRT/console play space.
- World size: about 4.20 units wide, 3.20 units deep, 2.60 units tall.
- Triangle budget: 22,000-62,000 triangles.
- Texture budget: one 512x512 nearest-filter texture atlas plus flat materials.
- Layout: one back wall with 10-15 taped posters, desk under the posters, bookshelf to the desk's left with a potted plant on top, wheeled lounge chair front-left of the desk, and disc rug beneath the chair.
- Desk clutter: CRT TV, PSX DVR-style console, three discs, table lamp, pens, eraser, and draft papers.
- Floor clutter: loose books and CD cases around the desk legs.
- Export: GLB, texture PNG, preview PNG, and Blender asset.

## Reusable Clutter Assets

Generate these as separate reusable assets and reuse instances inside `emi_room`:

- `poster`
- `draft_paper`
- `table_lamp`
- `pencil`
- `eraser`
- `potted_plant`
- `wheeled_lounge_chair`
- `floor_book`
- `cd_case`

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

The beanbag chair uses a rounded low-poly UV-sphere-derived cushion silhouette with a depressed center and radial fabric folds. It should read as one soft object, not a furniture assembly.

The disc rug uses a flat circular mat, dark rim, center label, green swirl fields, and original non-branded markings inspired by game discs and colored vinyl.

The `emi_room` scene uses the same palette and low-poly/PSX constraints while combining the individual assets with original room clutter. It should remain one importable room asset, not a replacement for the individual prop assets.

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
- `assets/3d/poster/poster.glb`
- `assets/3d/draft_paper/draft_paper.glb`
- `assets/3d/table_lamp/table_lamp.glb`
- `assets/3d/pencil/pencil.glb`
- `assets/3d/eraser/eraser.glb`
- `assets/3d/potted_plant/potted_plant.glb`
- `assets/3d/wheeled_lounge_chair/wheeled_lounge_chair.glb`
- `assets/3d/floor_book/floor_book.glb`
- `assets/3d/cd_case/cd_case.glb`
- `assets/3d/emi_room/emi_room.glb`
- `assets/3d/emi_room/emi_room_texture.png`
- `assets/3d/emi_room/emi_room_preview.png`
- `assets/3d/psx_dvr_assets_manifest.json`
- `assets/3d/psx_dvr_assets.blend`
- `assets/3d/psx_dvr_blender_import_report.json`
- `tools/create_psx_dvr_assets.py`
- `tools/test_psx_dvr_assets.py`

## Verification

- Run generator syntax checks.
- Run tests that fail before large-bezel CRT/single-body beanbag/disc-rug support exists and pass after implementation.
- Validate every generated GLB with the generator's `--verify` mode.
- Confirm `--report` enforces higher-detail budgets, five-head scale metadata, palette metadata, absence of `psx_dvr_crt_set`, CRT black-glass metadata, beanbag sit metadata, disc rug metadata, reusable clutter metadata, `emi_room` layout metadata, and relative size ordering.
- Visually inspect preview PNGs for non-empty, correctly framed assets.
- Regenerate the Blender scene and confirm it contains the 17 individual assets: `psx_dvr_console`, `psx_dvr_disc`, `crt_tv`, `bookshelf`, `desk`, `beanbag_chair`, `disc_rug`, `poster`, `draft_paper`, `table_lamp`, `pencil`, `eraser`, `potted_plant`, `wheeled_lounge_chair`, `floor_book`, `cd_case`, and `emi_room`.
