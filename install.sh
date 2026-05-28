#!/usr/bin/env bash

set -e

INSTALL_DIR="$HOME/.local/bin"
WAYBAR_CONFIG="$HOME/.config/waybar/config.jsonc"

mkdir -p "$INSTALL_DIR"

cp lyse.py "$INSTALL_DIR/lyse"
chmod +x "$INSTALL_DIR/lyse"

echo "Installed lyse to $INSTALL_DIR/lyse"

if [ ! -f "$WAYBAR_CONFIG" ]; then
    echo "Waybar config not found at $WAYBAR_CONFIG"
    echo "Skipping Waybar setup"
    exit 0
fi

cp "$WAYBAR_CONFIG" "$WAYBAR_CONFIG.bak"

if ! grep -q "custom/lyrics" "$WAYBAR_CONFIG"; then
    awk '
    /"modules-right"/ {
        print;
        getline;
        if ($0 ~ /\[/) {
            sub(/\[/, "[ \"custom/lyrics\", ", $0);
        }
        print;
        next;
    }
    {print}
    ' "$WAYBAR_CONFIG" > "$WAYBAR_CONFIG.tmp" && mv "$WAYBAR_CONFIG.tmp" "$WAYBAR_CONFIG"

    echo "Injected custom/lyrics into modules-right"
else
    echo "Waybar module already exists"
fi

if ! grep -q '"custom/lyrics"' "$WAYBAR_CONFIG"; then
    awk '
    /}/ {
        print "    ,\"custom/lyrics\": {\"exec\": \"cat /tmp/lyse\", \"interval\": 0.5}";
        print;
        next;
    }
    {print}
    ' "$WAYBAR_CONFIG" > "$WAYBAR_CONFIG.tmp" && mv "$WAYBAR_CONFIG.tmp" "$WAYBAR_CONFIG"

    echo "Added lyse config block"
else
    echo "Waybar config already exists"
fi

if pgrep waybar >/dev/null; then
    echo "Restarting Waybar..."

    pkill waybar

    sleep 0.3

    nohup waybar >/dev/null 2>&1 &

    echo "Waybar restarted"
else
    echo "Waybar not running, skipping restart"
fi

echo "Done"
