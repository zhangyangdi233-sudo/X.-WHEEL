# PSX DVR Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two logo-free PSX DVR-inspired low-poly GLB assets: a console and a matching optical disc.

**Architecture:** A single reproducible Python generator creates all geometry, materials, textures, GLB files, preview PNGs, and a manifest. Because Blender is not available in this environment, the source-of-truth file is the generator script rather than a `.blend` file.

**Tech Stack:** Python 3 standard library only, glTF 2.0 binary `.glb`, hand-authored PNG textures via `zlib`, simple orthographic software preview renderer.

---

## File Structure

- Create `tools/create_psx_dvr_assets.py`: geometry builders, PNG writer, GLB writer, preview renderer, manifest writer.
- Create `assets/3d/psx_dvr_console/psx_dvr_console.glb`: exported console asset.
- Create `assets/3d/psx_dvr_console/psx_dvr_console_texture.png`: 256x256 pixel texture atlas.
- Create `assets/3d/psx_dvr_console/psx_dvr_console_preview.png`: rendered preview.
- Create `assets/3d/psx_dvr_disc/psx_dvr_disc.glb`: exported optical disc asset.
- Create `assets/3d/psx_dvr_disc/psx_dvr_disc_texture.png`: 128x128 pixel texture atlas.
- Create `assets/3d/psx_dvr_disc/psx_dvr_disc_preview.png`: rendered preview.
- Create `assets/3d/psx_dvr_assets_manifest.json`: generated metadata with triangle counts, material counts, texture sizes, and known limitations.

## Task 1: Asset Generator

**Files:**
- Create: `tools/create_psx_dvr_assets.py`

- [ ] **Step 1: Write the generator script**

Create a Python script with these concrete units:

```python
def write_png(path, width, height, pixels):
    """Write RGBA PNG using only struct, binascii, and zlib."""

class MeshBuilder:
    def add_box(self, name, center, size, color, material_index):
        """Add hard-edged cuboid faces with duplicated vertices."""

    def add_cylinder(self, name, center, radius, depth, sides, color, material_index, hole_radius=0.0):
        """Add low-sided cylinder or ring geometry for discs and ports."""

def build_console_asset():
    """Return console meshes, materials, texture PNG data, and collision proxy."""

def build_disc_asset():
    """Return disc meshes, materials, texture PNG data, and collision proxy."""

def write_glb(path, asset):
    """Write glTF 2.0 binary with buffers, bufferViews, accessors, meshes, nodes, materials, and embedded texture image."""

def render_preview(path, asset, width=960, height=720):
    """Draw flat-shaded orthographic preview with z-sorted triangles."""

def main():
    """Create output directories, write textures, GLBs, previews, and manifest."""
```

- [ ] **Step 2: Run syntax check**

Run: `python -m py_compile tools/create_psx_dvr_assets.py`

Expected: exit code 0 and no output.

## Task 2: Generate Assets

**Files:**
- Create: `assets/3d/psx_dvr_console/psx_dvr_console.glb`
- Create: `assets/3d/psx_dvr_console/psx_dvr_console_texture.png`
- Create: `assets/3d/psx_dvr_console/psx_dvr_console_preview.png`
- Create: `assets/3d/psx_dvr_disc/psx_dvr_disc.glb`
- Create: `assets/3d/psx_dvr_disc/psx_dvr_disc_texture.png`
- Create: `assets/3d/psx_dvr_disc/psx_dvr_disc_preview.png`
- Create: `assets/3d/psx_dvr_assets_manifest.json`

- [ ] **Step 1: Run generator**

Run: `python tools/create_psx_dvr_assets.py`

Expected: console output listing both generated assets and triangle counts.

- [ ] **Step 2: Inspect generated file list**

Run: `rg --files assets/3d`

Expected output includes the two `.glb` files, two texture PNGs, two preview PNGs, and the manifest.

## Task 3: Verify GLB Structure

**Files:**
- Modify: `tools/create_psx_dvr_assets.py` only if validation exposes an exporter defect.

- [ ] **Step 1: Run built-in validation mode**

Run: `python tools/create_psx_dvr_assets.py --verify`

Expected: each GLB reports valid header, JSON chunk, BIN chunk, meshes, materials, embedded image, and byte-aligned bufferViews.

- [ ] **Step 2: Confirm metadata constraints**

Run: `python tools/create_psx_dvr_assets.py --report`

Expected:

```text
psx_dvr_console: triangles between 900 and 1800, texture 256x256
psx_dvr_disc: triangles between 200 and 700, texture 128x128
```

## Task 4: Final Review

**Files:**
- Read: `assets/3d/psx_dvr_assets_manifest.json`
- Read: generated preview PNGs.

- [ ] **Step 1: Review manifest**

Run: `Get-Content -LiteralPath 'assets\3d\psx_dvr_assets_manifest.json'`

Expected: manifest records object names, triangle counts, texture sizes, material counts, export paths, and limitation that `.blend` source is omitted because Blender is unavailable.

- [ ] **Step 2: Check git status**

Run: `git status --short`

Expected: only the generator, plan, and generated asset files are uncommitted.

## Self-Review

- Spec coverage: the plan covers separate console and disc assets, low-poly PSX style, GLB export, previews, texture sizes, triangle budgets, collision proxies, and metadata.
- Red-flag scan: no incomplete-work markers remain.
- Type consistency: the script units and verification commands refer to one file, `tools/create_psx_dvr_assets.py`, and the output paths match the design spec except `.blend` files, which are replaced by the generator due to unavailable Blender.
