#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
version=0.3.1
stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT HUP INT TERM
mkdir -p "$stage/DEBIAN" "$stage/usr/share/fcitx5-theme-studio/assets" "$stage/usr/bin" "$stage/usr/share/applications" "$stage/usr/share/icons/hicolor/scalable/apps" "$stage/usr/share/doc/fcitx5-theme-studio" "$project_dir/dist"
cp "$project_dir/studio.py" "$project_dir/theme_engine.py" "$project_dir/library_store.py" "$stage/usr/share/fcitx5-theme-studio/"
cp "$project_dir/assets/"*.svg "$stage/usr/share/fcitx5-theme-studio/assets/"
cp "$project_dir/assets/icon.svg" "$stage/usr/share/icons/hicolor/scalable/apps/fcitx5-theme-studio.svg"
cp "$project_dir/LICENSE" "$project_dir/README.md" "$project_dir/USER_GUIDE.md" "$stage/usr/share/doc/fcitx5-theme-studio/"
if [ -f "$project_dir/preview-day.png" ]; then
    cp "$project_dir/preview-day.png" "$stage/usr/share/doc/fcitx5-theme-studio/"
fi
cat > "$stage/DEBIAN/control" <<'CONTROL'
Package: fcitx5-theme-studio
Version: 0.3.1
Section: utils
Priority: optional
Architecture: all
Maintainer: Fcitx5 Theme Studio contributors <maintainers@example.invalid>
Depends: python3 (>= 3.10), python3-pyqt6, fcitx5, libglib2.0-bin
Recommends: libqt6svg6
Description: Visual Fcitx5 theme editor with portable designs
 Local editor with color presets, image placement, reserved decoration space,
 live previews, theme export, application and backup restoration.
CONTROL
cat > "$stage/usr/bin/fcitx5-theme-studio" <<'LAUNCH'
#!/bin/sh
exec /usr/bin/python3 /usr/share/fcitx5-theme-studio/studio.py "$@"
LAUNCH
chmod 755 "$stage/usr/bin/fcitx5-theme-studio"
cat > "$stage/usr/share/applications/fcitx5-theme-studio.desktop" <<'DESKTOP'
[Desktop Entry]
Name=Fcitx5 Theme Studio
Name[zh_CN]=输入法皮肤工坊
Comment=Design and share Fcitx5 candidate themes
Comment[zh_CN]=设计、预览和分享 Fcitx5 输入法皮肤
Exec=fcitx5-theme-studio
Icon=fcitx5-theme-studio
Type=Application
Categories=Settings;Utility;
Terminal=false
StartupNotify=true
DESKTOP
chmod -R u+rwX,go+rX,go-w "$stage"
dpkg-deb --build --root-owner-group "$stage" "$project_dir/dist/fcitx5-theme-studio_${version}_all.deb"
