# lyse-waybar

https://github.com/snoowfall/lyse

Realtime Waybar lyrics module for Spotify.

<img width="400" height="28" alt="preview" src="https://github.com/user-attachments/assets/d7492c68-0cb3-4c65-b5c4-b8a195c71d23" />

---

## What it is

lyse-waybar is a lightweight background script that:

- Reads your currently playing Spotify track via `playerctl`
- Fetches synced lyrics from LRCLIB
- Syncs lyrics in real time with playback position
- Caches lyrics locally for faster loading
- Outputs the current lyric line to `/tmp/lyse`

It is designed specifically for Waybar or similar status bars.

---

## Requirements

- `python 3`
- `playerctl`

---

## Install

`curl -sSL https://raw.githubusercontent.com/um0ra/lyse-waybar/main/install.sh | bash`
