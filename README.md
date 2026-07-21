# SnapAgent

SnapAgent is a Linux screenshot tool inspired by SnagIt:

- compact capture panel with delay
- full-screen, region, and window-under-cursor capture
- annotation tools: text, rectangle, circle, line, arrow
- alpha-enabled stroke and fill colors
- object selection, moving, and style updates after drawing
- zoom in/out with anchored drawing positions
- crop tool
- clipboard paste (`Ctrl+V`) for text, image, and image URL
- context menu with paste action
- undo/redo history
- save/load editable projects (`*.sfp`)
- export to PNG/JPEG/PDF
- print support
- English About and Shortcuts dialog
- auto-save every 30 seconds for opened project files
- first-run dependency installer with visible setup UI
- autostart checkbox in capture panel

## Requirements

- Python 3.11+
- Linux desktop environment with X11 tools for window capture:
  - `xdotool`
  - `xwininfo`

## Install

```bash
python3 run.py
```

On first start, SnapAgent creates `.venv`, installs dependencies, and then relaunches itself automatically.

## Run

```bash
python3 run.py
```

## View and Window Reference

This section defines the visible windows and UI element names used in SnapAgent.
It is intended for both end users and development discussions, so we can use the
same wording during further implementation.

## Visual UI Maps

The following wireframes provide a visual orientation for where each named element
is located. They are schematic (not pixel-perfect), but keep naming and positions
consistent for users and developers.

### Capture Panel Wireframe (`SnapAgent Capture`)

```text
+------------------------------------------------------+
| SnapAgent Capture                                  X |
+------------------------------------------------------+
| SnapAgent                                             |
|                                                      |
|  Delay:        [ 0 s      v ]                       |
|  Autostart:    [ ] Start at login                   |
|                                                      |
|  [Capture Fullscreen] [Capture Area] [Capture Window]|
+------------------------------------------------------+
```

### Editor Host + Tab Wireframe (`SnapAgent Editor`)

```text
+-----------------------------------------------------------------------------------+
| SnapAgent Editor                                                                X |
+-----------------------------------------------------------------------------------+
| [Screenshot 1] [Screenshot 2] [Screenshot 3]                                  [x]|
+-----------------------------------------------------------------------------------+
|                                                                                   |
|                (active Editor Tab content is rendered here)                       |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Editor Tab Wireframe (`Screenshot <n>`)

```text
+-----------------------------------------------------------------------------------+
| File  Edit  Help                                                                  |
+-----------------------------------------------------------------------------------+
| [Select][Rectangle][Circle][Line][Arrow][Text][Crop][Apply Crop]                 |
| [Stroke][Fill] Size[ 3 ] Font[16]  100%  Zoom[---|-----] [+] [-] [Reset]        |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|                               Canvas / Screenshot                                 |
|                   (draw, move, crop, paste, annotate, zoom)                      |
|                                                                                   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
| Status: Ready                                                                      |
+-----------------------------------------------------------------------------------+
```

### Region Capture Overlay Wireframe

```text
   (screen is dimmed)
   +---------------------------------------------------------------+
   |                                                               |
   |        +---------------------------------------------+        |
   |        |   Selected Area (drag rectangle)            |        |
   |        +---------------------------------------------+        |
   |                                                               |
   +---------------------------------------------------------------+
```

### Window Capture Overlay Wireframe

```text
   (screen is dimmed)
   +---------------------------------------------------------------+
   |                                                               |
   |   X:120 Y:90 W:1280 H:720                                     |
   |   +-------------------------------------------------------+   |
   |   |       Detected window under mouse cursor              |   |
   |   +-------------------------------------------------------+   |
   |                                                               |
   +---------------------------------------------------------------+
```

### System Tray Menu Wireframe

```text
SnapAgent (Tray Menu)
-------------------------------
Show SnapAgent
-------------------------------
Capture Area
Capture Window Under Cursor
-------------------------------
[x] Start at boot
-------------------------------
About
Quit SnapAgent
```

### 1) `SnapAgent Capture` (Capture Panel Window)

Purpose:
- Start new screenshots
- Configure capture delay
- Configure autostart behavior

Main elements:
- `Delay` (`QSpinBox`): Delay in seconds before capture starts.
- `Autostart` (`QCheckBox`): `Start at login`.
- `Capture Fullscreen` (`QPushButton`): Captures the full virtual desktop.
- `Capture Area` (`QPushButton`): Starts rectangle selection capture.
- `Capture Window` (`QPushButton`): Starts window-under-cursor capture.

Close behavior:
- Clicking window `X` minimizes to system tray (if tray is available).

### 2) `SnapAgent Editor` (Tabbed Editor Host Window)

Purpose:
- Host all screenshot editing sessions in tabs.

Main elements:
- `Editor Tabs` (`QTabWidget`): One tab per screenshot session (`Screenshot 1`, `Screenshot 2`, ...).
- Tab close button (`x`): Closes one screenshot editing tab.

Close behavior:
- Clicking window `X` minimizes to system tray (if tray is available).

### 3) `Screenshot <n>` (Editor Tab Content)

Purpose:
- Annotate and export a single captured screenshot.

Toolbar elements:
- Tool buttons: `Select`, `Rectangle`, `Circle`, `Line`, `Arrow`, `Text`, `Crop`
- Action button: `Apply Crop`
- Style buttons: `Stroke`, `Fill`
- Numeric controls: `Size`, `Font`
- Zoom controls: `+`, `-`, `Reset`

Menu bar:
- `File`:
  - `Open Project...`
  - `Save Project`
  - `Save Project As...`
  - `Export as PNG...`
  - `Export as JPEG...`
  - `Export as PDF...`
  - `Print...`
  - `Close`
- `Edit`:
  - `Undo`
  - `Redo`
  - `Paste`
- `Help`:
  - `About`
  - `Shortcuts & Manual`

Canvas behavior:
- Supports drawing, moving, selection, style updates, zoom, crop selection, and paste from clipboard (`Ctrl+V`).

### 4) Region Capture Overlay

Purpose:
- Select a rectangular area on the virtual desktop.

Visible elements:
- Dimmed desktop background
- Live selection rectangle while dragging

Controls:
- Left mouse drag/release: Confirm selected area.
- `Esc`: Cancel capture.

### 5) Window Capture Overlay

Purpose:
- Detect and capture the program window under the mouse cursor.

Visible elements:
- Highlight rectangle around detected target window
- Geometry label: `X:<...> Y:<...> W:<...> H:<...>`

Controls:
- Move mouse: Update target window.
- Left click: Capture exactly highlighted window area.
- `Esc`: Cancel capture.

### 6) System Tray Menu (`SnapAgent`)

Purpose:
- Keep the app running in background and provide quick actions.

Menu entries:
- `Show SnapAgent`
- `Capture Area`
- `Capture Window Under Cursor`
- `Start at boot` (checkbox)
- `About`
- `Quit SnapAgent`

Behavior:
- Tray icon click or double click restores visible windows.
- `Quit SnapAgent` exits the application completely.

### 7) First-Time Setup Window (`SnapAgent - First-time Setup`)

Purpose:
- Show dependency installation progress on first start (or repair run).

Visible elements:
- Status text (step-by-step)
- Indeterminate progress bar
- Hint text for privilege prompt

Related backend installer:
- `install_dependencies.py`

### Naming Conventions for Ongoing Development

Please use these exact names in issues, tasks, and feature requests:
- `Capture Panel`
- `Editor Host`
- `Editor Tab`
- `Region Overlay`
- `Window Overlay`
- `System Tray Menu`
- `First-Time Setup Window`

## Project Format

SnapAgent stores projects as ZIP-based `*.sfp` files:

- `manifest.json` with format/version, metadata, and annotations
- `assets/screenshot.png` for the base screenshot
- optional extra assets (for pasted images and future extensions)

The format is versioned and extensible for future features.

