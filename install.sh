#!/bin/sh
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
APPS_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

mkdir -p "$ICON_DIR" "$APPS_DIR" "$AUTOSTART_DIR"
cp "$APP_DIR/icons/traypresso_v2.svg" "$ICON_DIR/traypresso.svg"
sed "s|@APP_DIR@|$APP_DIR|" "$APP_DIR/traypresso.desktop.in" > "$APPS_DIR/traypresso.desktop"
ln -sf "$APPS_DIR/traypresso.desktop" "$AUTOSTART_DIR/traypresso.desktop"

command -v gtk-update-icon-cache >/dev/null && gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo "Installed. traypresso is in your application menu and will start on login."
