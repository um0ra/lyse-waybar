#!/usr/bin/env python3

# lyse-github | Realtime Waybar lyrics module for Spotify.

# https://github.com/snoowfall/lyse 

__version__ = "0.0.1"

#!/usr/bin/env python3

import time
import subprocess
import urllib.request
import urllib.parse
import json
import re
import os
import shutil
import random

LRCLIB_URL = "https://lrclib.net/api/get"
CACHE_DIR = os.path.expanduser("~/.cache/lyse")
OUT_FILE = "/tmp/lyse"


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


class LyseDaemon:
    def __init__(self):
        self.poller = poller()
        self.lyrics = []
        self.last_song = None
        self.loading = False
        self.last_output = ""

    def run(self):
        while True:
            try:
                track = self.poller.now_playing()

                if not track:
                    self._write("")
                    time.sleep(1)
                    continue

                song_id = track["trackid"]
                title = track["title"] or ""
                artist = track["artist"] or ""

                if "instrumental" in title.lower():
                    self._write("instrumental!")
                    time.sleep(1)
                    continue

                if song_id != self.last_song:
                    self.last_song = song_id
                    self.lyrics = []
                    self.loading = True

                    cached = self._load_cache(title, artist)

                    if cached:
                        self.lyrics = cached
                        self.loading = False
                    else:
                        self._write("getting lyrics...")
                        self._fetch(track)

                if not self.loading:
                    self._write(self._get_line(track["progress"]))

                time.sleep(0.5)

            except:
                self.loading = False
                self.lyrics = []
                self._write("ERR")
                time.sleep(1)

    def _write(self, text):
        if text is None:
            text = ""

        text = text.strip()

        if text == self.last_output:
            return

        self.last_output = text

        try:
            with open(OUT_FILE, "w") as f:
                f.write(text)
        except:
            pass

    def _load_cache(self, title, artist):
        path = cache_file_for(title, artist)

        try:
            with open(path) as f:
                data = json.load(f)

            return [(float(ts), t) for ts, t in data.get("lyrics", [])]
        except:
            return None

    def _save_cache(self, title, artist, lyrics):
        path = cache_file_for(title, artist)

        try:
            with open(path, "w") as f:
                json.dump(
                    {"lyrics": [[ts, text] for ts, text in lyrics]},
                    f,
                )
        except:
            pass

    def _fetch(self, track):
        try:
            def query(use_album=True):
                params = {
                    "track_name": track["title"],
                    "artist_name": track["artist"],
                    "duration": int(track["duration"]),
                }

                if use_album:
                    params["album_name"] = track["album"]

                url = f"{LRCLIB_URL}?{urllib.parse.urlencode(params)}"

                with urllib.request.urlopen(url, timeout=8) as r:
                    return json.loads(r.read())

            def collect(data):
                out = []

                if isinstance(data, list):
                    for e in data:
                        self._collect(e, out)
                elif isinstance(data, dict):
                    self._collect(data, out)

                return out

            data = query(True)
            candidates = collect(data)

            if not candidates:
                data = query(False)
                candidates = collect(data)

            if not candidates:
                self.loading = False
                self.lyrics = []
                self._write("")
                return

            scored = []

            for entry, lyrics in candidates:
                score = self._score(entry, track)
                scored.append((score, lyrics))

            best = max(s[0] for s in scored)
            pool = [x for x in scored if abs(x[0] - best) < 1e-6]

            _, lyrics = random.choice(pool)

            self.lyrics = lyrics
            self.loading = False

            self._save_cache(track["title"], track["artist"], lyrics)

        except:
            self.loading = False
            self.lyrics = []
            self._write("ERR")

    def _collect(self, entry, out):
        lrc = entry.get("syncedLyrics")
        if not lrc:
            return

        parsed = self._parse_lrc(lrc)
        if parsed:
            out.append((entry, parsed))

    def _score(self, entry, track):
        def norm(s):
            return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

        def sim(a, b):
            from difflib import SequenceMatcher
            return SequenceMatcher(None, norm(a), norm(b)).ratio()

        t = entry.get("trackName") or ""
        a = entry.get("artistName") or ""
        d = entry.get("duration") or 0

        ts = sim(track["title"], t)
        as_ = sim(track["artist"], a)

        ds = 0
        if track["duration"] and d:
            diff = abs(track["duration"] - float(d))
            ds = max(0.0, 1.0 - diff / max(track["duration"], 1))

        return ts * 0.55 + as_ * 0.4 + ds * 0.05

    def _parse_lrc(self, lrc):
        out = []

        for line in lrc.splitlines():
            matches = re.findall(r"\[(\d+):(\d+\.?\d*)\]", line)
            if not matches:
                continue

            text = re.sub(r"\[.*?\]", "", line).strip() or "♪"

            for m in matches:
                out.append((int(m[0]) * 60 + float(m[1]), text))

        return sorted(out)

    def _get_line(self, progress):
        if not self.lyrics:
            return ""

        cur = "♪"
        for ts, text in self.lyrics:
            if ts > progress:
                break
            cur = text

        return cur.strip() or "♪"


def main():
    if not shutil.which("playerctl"):
        print("playerctl not found")
        return

    LyseDaemon().run()


if __name__ == "__main__":
    main()
