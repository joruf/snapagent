# Snappix

Snappix is a Linux screenshot and annotation app inspired by SnagIt.  
Capture quickly, annotate in a tabbed editor, and keep projects editable as `.sfp` files.

**[Technical Documentation](docs/TECHNICAL.md)** — architecture, modules, config schema, capture pipeline, annotation model

---

## Install and Run

```bash
git clone https://github.com/joruf/snappix.git
cd snappix
python3 run.py
```

On first start Snappix creates a local `.venv`, installs Python packages, checks system dependencies, and relaunches automatically.

### Manual system packages (if the first-run installer is blocked)

```bash
# Debian / Ubuntu
sudo apt install libxcb-cursor0 python3-tk python3-venv xdotool x11-utils tesseract-ocr grim slurp
```

| Package | Why |
|---------|-----|
| `libxcb-cursor0` | Qt cursor support |
| `python3-tk` / `python3-venv` | First-run installer UI and venv |
| `xdotool`, `x11-utils` | Window / scroll capture on X11 |
| `tesseract-ocr` | OCR tool |
| `grim`, `slurp` | Recommended for Wayland region / fullscreen capture |

### Requirements

- Python **3.11+**
- Linux desktop (X11 or Wayland)
- Python packages (installed into `.venv`): PySide6, Pillow, requests, pynput

### Packages / releases

```bash
# Debian package
./packaging/build_deb.sh 0.1.0

# AppImage
./packaging/build_appimage.sh 0.1.0
```

Artifacts land in `dist/`. Tag `v1.2.0` (or run **Release Build** in GitHub Actions) to publish `.deb` and AppImage.

---

## Key Features

### Capture

- Compact **Capture Panel** with delay (0–20 s)
- Modes: **Fullscreen**, **Area**, **Window**, **Scroll**, **Color Picker**
- **Auto scroll capture** for long pages (scrollbar detect + stitch)
- Post-capture: open editor, copy clipboard, or save to folder
- Global hotkeys (default `Ctrl+Shift+A/W/F`)
- Wayland region capture via `grim` + `slurp` when available

### Editor

- Tabbed **Editor Host** for multiple screenshots
- Drawing tools: Select, Rectangle, Ellipse, Line, Arrow, Text, Step, Crop
- Pixel tools: Rect/Ellipse/Lasso selection, Magic Wand, Brush, Eraser, Fill, Eyedropper
- Redaction: **Blur**; background paint: **Bg Fill**; **OCR** region → clipboard
- **Per-tool menus** (like Width): Hard (Brush/Eraser), Style solid/dash/dot (shapes/lines)
- Text tool menu: font, size, plain / box / bubble, spacing, padding
- One-shot tools → return to Select; **double-click** locks a tool
- Layers, geometry inspector (`X/Y/W/H`), document footer when nothing is selected
- History with labeled undo list; zoom, grid, snap, smart guides
- Export PNG / JPEG / PDF, batch export profiles, print
- Multi-tab session recovery (auto-save every 30 s)

### Desktop integration

- Single-instance lock, system tray, autostart (XDG)
- Light / Dark themes
- Settings: hotkeys, post-capture action, save folder, editor shortcuts, auto-crop

---

## Screenshots

### Capture Panel

![Snappix Capture Panel](docs/screenshots/capture-panel.png)

### Region Overlay

![Snappix Region Overlay](docs/screenshots/region-overlay.png)

### Window Overlay

![Snappix Window Overlay](docs/screenshots/capture-window-preview.png)

### Editor Window

![Snappix Editor Window](docs/screenshots/editor-window.png)

### System Tray Menu

![Snappix System Tray Menu](docs/screenshots/system-tray-menu.png)

### First-Time Setup

![Snappix First-Time Setup](docs/screenshots/first-time-setup.png)

Regenerate after UI changes:

```bash
.venv/bin/python scripts/generate_readme_screenshots.py
```

---

## Usage

### Capture Panel

| Control | Action |
|---------|--------|
| Capture Fullscreen | Full virtual desktop |
| Capture Area | Drag-selection overlay |
| Capture Window | X11 window pick (on Wayland prefer Area/Scroll) |
| Scroll | Auto-scroll + stitch long content |
| Color picker | Sample screen color → clipboard |
| Open Editor | Editor host / blank canvas |

### Scroll Capture

1. Click **Scroll** and select the target window.
2. Snappix finds the scrollbar, scrolls from top to bottom, and stitches frames.
3. The result opens in the editor. Press **Esc** during window pick to cancel.

### Editor tools (overview)

| Tool | Notes |
|------|--------|
| Brush / Eraser | Soft stamps; **Width** + **Hard** in the tool menu |
| Line / Arrow / Rect / Ellipse | **Width** + **Style** (solid/dash/dot/dash-dot) in the tool menu |
| Text | Typography in the Text tool menu |
| Blur | Pixel-block size in the Blur tool menu |
| Magic Wand / selections | Tolerance and erase mode in tool menus |
| Step | Numbered tutorial badges |
| OCR | Drag a region; text copied to clipboard |

### Settings

**View → Settings** (editor) or tray **Settings**:

- Global hotkeys on/off and bindings
- Action after capture (editor / clipboard / save)
- Capture save folder (default `~/Downloads/snappix/`)
- Editor keyboard shortcut overrides
- Auto-crop unused canvas margins

---

## CLI

```bash
# Fullscreen PNG
python3 run.py capture --mode full_screen --delay 1 --output /tmp/shot

# Interactive region or window
python3 run.py capture --mode region --output /tmp/area.png
python3 run.py capture --mode window --output /tmp/window.png

# Color picker
python3 run.py pick-color --clipboard

# Export project
python3 run.py export --project ./example.sfp --format jpg --preset docs --output ./export.jpg
python3 run.py export --project ./example.sfp --format pdf --preset print --output ./export.pdf

# Batch export
python3 run.py batch-export \
  --project ./a.sfp \
  --project ./b.sfp \
  --formats png jpg pdf \
  --preset web \
  --output-dir ./exports

# Open project in the GUI
python3 run.py open --project ./example.sfp
```

---

## Keyboard Shortcuts

### Editor (defaults; configurable in Settings)

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New canvas |
| `Ctrl+T` | New empty tab |
| `Ctrl+O` | Open project |
| `Ctrl+S` / `Ctrl+Shift+S` | Save / Save as |
| `Ctrl+Shift+E` | Export |
| `Ctrl+P` | Print |
| `Ctrl+W` | Close tab |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` / `Ctrl+Shift+Z` | Redo |
| `Ctrl+D` | Duplicate selection |
| `Ctrl+C` / `Ctrl+V` | Copy / Paste |
| `Ctrl+Shift+C` / `Ctrl+Shift+V` | Copy / paste drawing area across tabs |
| `Ctrl++` / `Ctrl+-` / `Ctrl+0` | Zoom in / out / reset |
| `Ctrl+Shift++` / `Ctrl+Shift+-` | Grow / shrink selection |
| `Enter` | Apply crop |
| `Esc` | Cancel crop / overlay |

### Global (default)

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+A` | Capture area |
| `Ctrl+Shift+W` | Capture window |
| `Ctrl+Shift+F` | Capture fullscreen |

---

## Project Format

Projects are ZIP-based `*.sfp` files:

- `manifest.json` — metadata and annotations
- `assets/screenshot.png` — base image
- optional `assets/image-*.png` — pasted images

Payload fields include `stroke_style`, `text_style`, `z_index`, `step_number`, transforms.  
Details: [Technical Documentation → Annotation Model](docs/TECHNICAL.md#annotation-model).

User config: `~/.config/snappix/config.json`  
Schema: [Technical Documentation → Configuration](docs/TECHNICAL.md#configuration).

Multi-tab recovery lives under `/tmp/snappix-session/` (auto-save every 30 s).

---

## Testing

```bash
.venv/bin/python -m unittest discover -s tests -v
```

---

## License

See the repository license file for terms.
