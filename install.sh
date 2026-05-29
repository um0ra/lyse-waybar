#!/usr/bin/env bash

set -e

REPO="https://raw.githubusercontent.com/um0ra/lyse-waybar/main"

INSTALL_DIR="$HOME/.local/bin"
WAYBAR_CONFIG="$HOME/.config/waybar/config.jsonc"

mkdir -p "$INSTALL_DIR"

echo "Downloading lyse..."

curl -sSL "$REPO/lyse.py" -o "$INSTALL_DIR/lyse"
chmod +x "$INSTALL_DIR/lyse"

echo "Installed to $INSTALL_DIR/lyse"

# ---------------- Waybar config ----------------

if [ ! -f "$WAYBAR_CONFIG" ]; then
    echo "Waybar config not found, skipping config step"
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
fi

if ! grep -q '"custom/lyrics"' "$WAYBAR_CONFIG"; then
    awk '
    /}/ {
        print "    ,\"custom/lyrics\": {\"exec\": \"~/.local/bin/lyse\", \"return-type\": \"json\", \"interval\": 0.3, \"format\": \"{text}\"}";
        print;
        next;
    }
    {print}
    ' "$WAYBAR_CONFIG" > "$WAYBAR_CONFIG.tmp" && mv "$WAYBAR_CONFIG.tmp" "$WAYBAR_CONFIG"
fi

# ---------------- restart waybar ----------------

if pgrep waybar >/dev/null; then
    echo "Restarting Waybar..."
    pkill waybar
    sleep 0.3
    nohup waybar >/dev/null 2>&1 &
fi

echo "Done"
