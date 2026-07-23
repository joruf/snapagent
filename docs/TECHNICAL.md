# Snappix Technical Documentation

Architecture, modules, data formats, and extension points for developers.

## Overview

Snappix is a Linux desktop app (Python 3.11+, PySide6 / Qt 6) with a controller-driven layout:

```text
run.py (AppController)
├── CapturePanel + overlays (src/capture.py)
├── EditorHostWindow + EditorWindow tabs (run.py, src/editor_window.py)
├── System tray + settings (run.py, src/settings_dialog.py)
├── Config (src/config.py) + shortcuts (src/shortcuts.py)
├── Session recovery (src/session_recovery.py)
├── Global hotkeys (src/global_hotkeys.py)
└── Theme engine (src/theme.py)
```

Single-instance lock: `~/.cache/snappix/snappix.lock`.

## Entry Points

| Entry | File | Purpose |
|-------|------|---------|
| Main GUI | `run.py` | Tray, capture/editor host, post-capture routing |
| Package | `src/__main__.py` | `python -m src` |
| CLI | `src/cli.py` | Headless capture, export, open |
| Installer | `install_dependencies.py` | `.venv`, system packages, pip deps |
| Installer UI | `src/install_progress_gui.py` | Tk progress during first-run setup |

Startup:

1. Re-exec into `.venv` when present.
2. Ensure PySide6 (Tk installer UI if missing).
3. Acquire single-instance lock.
4. Create `QApplication`, load config, apply theme.
5. Show capture panel; optionally restore multi-tab session or open a startup project.

## Source Module Map

| Module | Responsibility |
|--------|----------------|
| `run.py` | `AppController`, tray, editor host tabs, hotkeys, session flush |
| `src/capture.py` | Capture panel, region/window overlays, color picker, capture engine |
| `src/auto_scroll_capture.py` | Automatic window scroll + frame collection |
| `src/scroll_capture.py` | Vertical stitch / overlap detection |
| `src/editor_window.py` | Editor chrome, toolbars, property tabs, history, export/print |
| `src/editor_canvas.py` | Canvas tools, zoom, crop, paste, OCR region, document footer |
| `src/brush_paint.py` | Soft brush/eraser stamps (hardness, opacity) |
| `src/pixel_selection.py` | Raster selection masks for wand/brush clip/fill |
| `src/annotation_items.py` | Serialization, pens, arrows, scene conversion |
| `src/annotation_shapes.py` | `StepBadgeItem`, `StyledTextItem` (plain/box/bubble) |
| `src/crop_item.py` | Crop frame + resize overlay handles |
| `src/models.py` | `AnnotationModel`, `ProjectModel` |
| `src/storage.py` | `.sfp` ZIP save/load (deep-copied payloads on save) |
| `src/session_recovery.py` | Per-tab recovery paths + session manifest |
| `src/config.py` | User JSON config, per-tool width/hardness/style maps |
| `src/shortcuts.py` | Editor shortcut definitions and conflict checks |
| `src/settings_dialog.py` | Hotkeys, post-capture, save folder, shortcut editors |
| `src/theme.py` | Light/dark QSS + capture/editor accent sheets |
| `src/global_hotkeys.py` | `pynput` global shortcuts → Qt signals |
| `src/image_effects.py` | Pixelation for blur redaction |
| `src/ocr.py` | Tesseract CLI wrapper |
| `src/platform.py` | Wayland detection, grim/slurp, tesseract checks |
| `src/cli.py` | Non-GUI commands |
| `src/autostart.py` | XDG autostart `.desktop` |
| `src/tool_reference.py` / `tool_reference_dialog.py` | In-app tools help |
| `src/new_canvas_dialog.py` | Blank canvas size picker |
| `src/canvas_size.py` | Canvas size helpers |
| `src/constants.py` | App name, `.sfp` extension, format version |

## Capture Pipeline

### Modes

| Mode | Constant | Description |
|------|----------|-------------|
| Fullscreen | `CaptureMode.FULL_SCREEN` | Virtual desktop composite |
| Region | `CaptureMode.REGION` | Drag selection overlay |
| Window | `CaptureMode.WINDOW` | X11 window via `xdotool` |
| Scroll | `CaptureMode.SCROLL` | Auto-scroll + vertical stitch |
| Color pick | N/A | Full-screen eyedropper overlay |

### Region

1. Snapshot virtual desktop.
2. Show `RegionCaptureOverlay`.
3. On release, crop and emit pixmap.

On Wayland with `grim`/`slurp`, native tools may replace the Qt overlay.

### Window (X11)

1. Desktop snapshot.
2. `xdotool selectwindow` + `xwininfo` geometry.
3. Crop to window rect.

On Wayland, window capture is not reliable; the UI recommends Area or Scroll.

### Scroll

1. Window pick (same as window capture).
2. `perform_auto_scroll_capture()` detects scrollbar, scrolls top→bottom, captures frames.
3. `src/scroll_capture.py` stitches with overlap detection.
4. Result opens in the editor; **Esc** cancels during pick.

### Post-capture actions

| Config value | Behavior |
|--------------|----------|
| `editor` | New editor tab (default) |
| `clipboard` | Copy pixmap |
| `save` | PNG to configured or `~/Downloads/snappix/` |

## Editor Architecture

### Host

`AppController` owns `EditorHostWindow` with a closable `QTabWidget`. Each tab is an `EditorWindow` (embedded `QMainWindow`).

### Canvas

`EditorCanvas` (`QGraphicsView`):

- Screenshot background item + gray workspace chrome outside the document
- Annotation items tagged with `ITEM_ROLE_TYPE = 1001`
- Tool state machine, crop, pixel selection, soft brush buffer
- Document footer payload when nothing is selected (`type: document`)
- Content changes emit labels used for history and one-shot tool completion

### Tool identifiers

| Tool ID | Description |
|---------|-------------|
| `select` | Move / select annotations |
| `select_rect` / `select_ellipse` / `select_path` | Pixel selection shapes / lasso |
| `magic_wand` | Color-based pixel selection |
| `brush` / `eraser` | Soft freehand paint / erase |
| `bucket` | Fill active pixel selection |
| `eyedropper` | Sample border or fill color |
| `rect` / `ellipse` / `line` / `arrow` | Vector annotations |
| `text` | Plain / box / bubble text |
| `fill_bg` | Paint rectangle on screenshot pixels |
| `blur` | Pixelate region |
| `step` | Numbered badge |
| `ocr` | OCR region → clipboard |
| `crop` | Non-destructive crop |

### Drawing modes

- **One-shot:** After a completed draw action, switch back to Select (unless locked).
- **Lock:** Double-click a lockable tool to keep it until clicked again or another tool is chosen.
- Auto-fit of the document keeps the original draw label so one-shot still fires.

### Per-tool defaults (persisted)

Stored in `config.json` and restored on tool switch / editor open:

| Map | Tools | UI |
|-----|-------|-----|
| `tool_stroke_widths` | brush, eraser, rect, ellipse, line, arrow, text | Tool popup **Width** |
| `tool_brush_hardness` | brush, eraser | Tool popup **Hard** |
| `tool_stroke_styles` | rect, ellipse, line, arrow | Tool popup **Style** |

With a matching selection, Width/Style updates apply to selected items instead of only the tool default.

### Style state

`StyleState` (`src/annotation_items.py`): stroke/fill/text colors, width, stroke style, font, text container style, letter/line spacing, box padding, corner radius.

### Layers and geometry

- Z-order in `payload.z_index`
- Layer combo: visibility / lock / reorder
- Geometry spins: `X/Y/W/H` apply to selection
- Status footer: selection summary or document size / zoom / annotation count

### History and autosave

- Undo/redo: full canvas snapshots (screenshot + annotations + base content origin)
- Per-tab recovery: `flush_recovery_snapshot()` every 30 s (`QObject.startTimer`)
- Session manifest: `/tmp/snappix-session/session.json` + `tab-<uuid>.sfp`
- Autosave guards against deleted Qt wrappers (`shiboken6.isValid`) and overlapping flushes

## Annotation Model

| Field | Type | Notes |
|-------|------|-------|
| `annotation_type` | str | `rect`, `ellipse`, `line`, `arrow`, `text`, `image`, `step` |
| `x`, `y`, `width`, `height` | float | Scene geometry |
| `stroke_rgba`, `fill_rgba` | list[int] | RGBA 0–255 |
| `stroke_width` | float | `0` → NoPen for shapes/text borders |
| `text` / `font_*` | various | Text / step content |
| `payload` | dict | `stroke_style`, `text_style`, `z_index`, `step_number`, transforms, `image_png_base64` |

Custom items: `StepBadgeItem`, `StyledTextItem`, `ArrowItem`.

## Project Storage (`.sfp`)

`PROJECT_FORMAT_VERSION = 3`

ZIP (`ZIP_DEFLATED`):

| Path | Content |
|------|---------|
| `manifest.json` | Metadata + annotations |
| `assets/screenshot.png` | Base screenshot |
| `assets/image-*.png` | Externalized pasted images |

`save_project` deep-copies annotation payloads before stripping image bytes so live models stay intact across autosaves.

Legacy JSON / `.lshot` still load.

## Configuration

Path: `~/.config/snappix/config.json`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `autostart_enabled` | bool | `false` | XDG autostart |
| `theme` | str | `"dark"` | `dark` / `light` |
| `hotkeys_enabled` | bool | `true` | Global shortcuts |
| `hotkey_capture_region` | str | `ctrl+shift+a` | Area hotkey |
| `hotkey_capture_window` | str | `ctrl+shift+w` | Window hotkey |
| `hotkey_capture_fullscreen` | str | `ctrl+shift+f` | Fullscreen hotkey |
| `post_capture_action` | str | `editor` | Post-capture routing |
| `capture_save_directory` | str | `""` | Save folder override |
| `editor_last_tab_behavior` | str | `keep_open` | Last-tab close behavior |
| `export_preset` | str | `docs` | Last export preset |
| `export_scale` | float | `1.0` | Export scale 1 / 2 / 3 |
| `export_keep_transparency` | bool | `true` | PNG alpha |
| `batch_export_profiles` | list | built-ins | Named batch profiles |
| `batch_export_profile_key` | str | `docs_hq` | Active batch profile |
| `batch_export_last_directory` | str | `""` | Last batch output dir |
| `auto_crop_on_shrink` | bool | `true` | Shrink unused canvas margins |
| `editor_shortcuts` | dict | `{}` | Shortcut overrides |
| `tool_stroke_widths` | dict | see defaults | Per-tool widths |
| `tool_brush_hardness` | dict | brush/eraser `80` | Per-tool hardness |
| `tool_stroke_styles` | dict | all `solid` | Per-tool line styles |

## Theming

`src/theme.py` builds global QSS plus capture-red and editor-blue accent overrides (`build_capture_accent_stylesheet`, `build_editor_accent_stylesheet`).

Notable object names: `primaryButton`, `linkButton`, `mutedLabel`, `titleLabel`, `editorToolbar`, `editorHost`.

## Global Hotkeys

`src/global_hotkeys.py` + `pynput`. Specs normalize to lowercase (`ctrl+shift+a`) and map to pynput syntax. Callbacks hop to the Qt thread via `HotkeyBridge`.

Reliable on X11; Wayland depends on the compositor.

## Platform Support

| Feature | X11 | Wayland |
|---------|-----|---------|
| Fullscreen | Yes | Yes (Qt / grim) |
| Region | Overlay | Overlay or grim+slurp |
| Window | xdotool | Not supported |
| Scroll | Yes | Limited / best-effort |
| Global hotkeys | pynput | Limited |
| Color picker | Overlay | Overlay |

## OCR

1. OCR tool → drag region.
2. Composited crop → temp PNG.
3. `tesseract` CLI → clipboard (+ status bar message).

Requires `tesseract` on `PATH`.

## CLI

| Command | Description |
|---------|-------------|
| `capture` | `--mode`, `--delay`, `--output` |
| `pick-color` | Optional `--clipboard` |
| `export` | Project → PNG/JPG/PDF |
| `batch-export` | Multiple projects/formats |
| `open` | GUI with project |

## Testing

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Coverage includes config/storage, annotations, brush freeze guards, canvas resize/workspace, editor history/one-shot/lock, selection footer, tool menus (width/hardness/style), theme, hotkeys, scroll stitch, session recovery, installer helpers, and E2E editor flows.

Prefer deterministic unit tests over live X11 smoke as the release gate.

## Packaging

| Script | Output |
|--------|--------|
| `packaging/build_deb.sh` | `dist/snappix_{version}_{arch}.deb` |
| `packaging/build_appimage.sh` | `dist/Snappix-{version}-x86_64.AppImage` |

Screenshots for README: `scripts/generate_readme_screenshots.py` → `docs/screenshots/`.

## Dependencies

| Package | Purpose |
|---------|---------|
| PySide6 | Qt 6 GUI |
| Pillow | Image helpers |
| requests | Paste image from URL |
| pynput | Global hotkeys |

## Extension Points

| Goal | Where |
|------|--------|
| New annotation type | `annotation_items.py`, `annotation_shapes.py`, `EditorCanvas` |
| New capture mode | `CaptureMode` + `execute_capture_request()` |
| New export format | `EditorWindow` export helpers + CLI |
| New setting | `AppConfig` + `ConfigManager` + `SettingsDialog` |
| Per-tool option | Tool popup in `EditorWindow` + normalize helpers in `config.py` |
| Theme token | `ThemeColors` + stylesheet builders |

## Known Limitations

- PDF export uses `QPdfWriter`; behavior can vary by PySide6 build.
- Window capture needs X11 tooling.
- Scroll stitch assumes mostly vertical scroll with overlapping frames.
- OCR quality depends on Tesseract language packs and image clarity.
- Embedding `QMainWindow` tabs is intentional but unusual; destroy/autosave paths must keep Qt object validity checks.
