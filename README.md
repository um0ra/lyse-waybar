# lyse-waybar

https://github.com/snoowfall/lyse

Realtime Waybar lyrics module for Spotify.

<img width="1250" height="901" alt="preview" src="https://github.com/user-attachments/assets/246943a6-0c90-4aea-b67f-9032337c4539" />

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

### Arch Linux (AUR)
```bash
yay -S lyse-waybar
# or
paru -S lyse-waybar
