#!/usr/bin/env python3

import subprocess
import urllib.request
import urllib.parse
import json
import re
import os
import shutil

LRCLIB_URL = "https://lrclib.net/api/get"
CACHE_DIR = os.path.expanduser("~/.cache/lyse")

def cache_file_for(title, artist):
    os.makedirs(CACHE_DIR, exist_ok=True)

    def norm(s):
        return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")

    return os.path.join(CACHE_DIR, f"{norm(artist)}_{norm(title)}.json")

class poller:
    def _cmd(self, args):
        try:
            out = subprocess.check_output(
                ["playerctl", "--player=spotify"] + args,
                stderr=subprocess.DEVNULL,
            )
            return out.decode(errors="replace").strip()
        except:
            return None

    def now_playing(self):
        status = self._cmd(["status"])
        if status not in ("Playing", "Paused"):
            return None

        sep = "\x1f"
        fmt = (
            f"{{{{mpris:trackid}}}}{sep}"
            f"{{{{title}}}}{sep}"
            f"{{{{artist}}}}{sep}"
            f"{{{{album}}}}{sep}"
            f"{{{{mpris:length}}}}"
        )

        meta = self._cmd(["metadata", "--format", fmt])
        if not meta:
            return None

        parts = meta.split(sep)
        if len(parts) < 5:
            return None

        trackid, title, artist, album, length = parts

        try:
            duration = int(length) / 1_000_000
        except:
            duration = 0

        try:
            pos = float(self._cmd(["position"]) or "0")
        except:
            pos = 0

        return {
            "trackid": trackid,
            "title": title,
            "artist": artist,
            "album": album,
            "duration": duration,
            "progress": pos,
        }

class Lyse:
    def run(self):
        track = poller().now_playing()

        if not track:
            print(json.dumps({"text": ""}))
            return

        title = track["title"] or ""
        artist = track["artist"] or ""

        if "instrumental" in title.lower():
            print(json.dumps({"text": "instrumental"}))
            return

        lyrics = self._get_lyrics(track)

        if not lyrics:
            print(json.dumps({"text": ""}))
            return

        line = self._get_line(lyrics, track["progress"])

        print(json.dumps({"text": line}))

    def _get_lyrics(self, track):
        cached = self._load_cache(track["title"], track["artist"])
        if cached:
            return cached

        try:
            params = {
                "track_name": track["title"],
                "artist_name": track["artist"],
                "duration": int(track["duration"]),
                "album_name": track["album"],
            }

            url = f"{LRCLIB_URL}?{urllib.parse.urlencode(params)}"

            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())

            lyrics = self._collect(data)

            if lyrics:
                self._save_cache(track["title"], track["artist"], lyrics)

            return lyrics

        except:
            return []

    def _collect(self, data):
        out = []

        def parse_entry(entry):
            lrc = entry.get("syncedLyrics")
            if not lrc:
                return

            for line in lrc.splitlines():
                matches = re.findall(r"\[(\d+):(\d+\.?\d*)\]", line)
                if not matches:
                    continue

                text = re.sub(r"\[.*?\]", "", line).strip() or "♪"

                for m in matches:
                    ts = int(m[0]) * 60 + float(m[1])
                    out.append((ts, text))

        if isinstance(data, list):
            for e in data:
                parse_entry(e)
        elif isinstance(data, dict):
            parse_entry(data)

        return sorted(out)

    def _load_cache(self, title, artist):
        path = cache_file_for(title, artist)

        try:
            with open(path) as f:
                data = json.load(f)

            return [(float(t), x) for t, x in data.get("lyrics", [])]
        except:
            return None

    def _save_cache(self, title, artist, lyrics):
        path = cache_file_for(title, artist)

        try:
            with open(path, "w") as f:
                json.dump(
                    {"lyrics": [[t, x] for t, x in lyrics]},
                    f,
                )
        except:
            pass

    def _get_line(self, lyrics, progress):
        cur = ""

        for ts, text in lyrics:
            if ts > progress:
                break
            cur = text

        return cur or "♪"

if __name__ == "__main__":
    Lyse().run()
