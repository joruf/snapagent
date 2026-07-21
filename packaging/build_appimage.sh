#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
BUILD_DIR="$PROJECT_ROOT/.build/appimage"
APPDIR="$BUILD_DIR/SnapAgent.AppDir"
APP_VERSION="${1:-0.1.0}"

if ! command -v appimagetool >/dev/null 2>&1; then
  echo "appimagetool not found. Install it first."
  exit 1
fi

echo "[snapagent] Preparing AppDir..."
rm -rf "$BUILD_DIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/snapagent"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"

echo "[snapagent] Copying application files..."
rsync -a \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude ".build" \
  --exclude "dist" \
  --exclude "__pycache__" \
  "$PROJECT_ROOT/" "$APPDIR/usr/share/snapagent/"

cat > "$APPDIR/AppRun" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec "$APPDIR/usr/bin/snapagent" "$@"
EOF
chmod 0755 "$APPDIR/AppRun"

cat > "$APPDIR/usr/bin/snapagent" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec python3 "$APPDIR/usr/share/snapagent/run.py" "$@"
EOF
chmod 0755 "$APPDIR/usr/bin/snapagent"

cat > "$APPDIR/snapagent.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=SnapAgent
Comment=Screenshot and annotation tool
Exec=snapagent
Icon=snapagent
Terminal=false
Categories=Graphics;Utility;
StartupWMClass=snapagent
EOF

cp "$APPDIR/snapagent.desktop" "$APPDIR/usr/share/applications/snapagent.desktop"
cp "$PROJECT_ROOT/assets/snapagent.svg" "$APPDIR/snapagent.svg"
cp "$PROJECT_ROOT/assets/snapagent.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/snapagent.svg"

mkdir -p "$DIST_DIR"
OUTPUT_FILE="$DIST_DIR/SnapAgent-${APP_VERSION}-x86_64.AppImage"
echo "[snapagent] Building AppImage: $OUTPUT_FILE"
ARCH=x86_64 appimagetool "$APPDIR" "$OUTPUT_FILE"
echo "[snapagent] Done."
