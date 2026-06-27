#!/usr/bin/env python3
"""
organize_home.py — Unified home + Downloads organizer
6 shared destination folders, same rules for both sources.

Usage:
  python organize_home.py                    # dry run ~ (home)
  python organize_home.py --run              # apply to ~
  python organize_home.py --downloads        # dry run ~/Downloads
  python organize_home.py --downloads --run  # apply to ~/Downloads
  python organize_home.py --all              # dry run both
  python organize_home.py --all --run        # apply to both
  python organize_home.py --undo             # undo last run
"""

import re
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime

HOME = Path.home()
LOG_FILE = HOME / "c0d3/Utility-Scripts/move_log.json"

# ── 6 flat destinations (same for home and Downloads) ─────────────────────────
DEST = {
    "media":     HOME / "Media",
    "documents": HOME / "Documents",
    "archives":  HOME / "Archives",
    "models":    HOME / "Models",
    "dev":       HOME / "Dev",
    "logs":      HOME / "Logs",
}

# ── Extension → bucket ───────────────────────────────────────────────────────
EXT_MAP = {
    # media
    ".jpg": "media", ".jpeg": "media", ".png": "media", ".gif": "media",
    ".webp": "media", ".bmp": "media", ".ico": "media", ".svg": "media",
    ".heic": "media",
    ".mp4": "media", ".avi": "media", ".mkv": "media", ".mov": "media",
    ".webm": "media",
    ".mp3": "media", ".wav": "media", ".flac": "media", ".ogg": "media",
    ".aac": "media",
    # documents
    ".pdf": "documents", ".docx": "documents", ".doc": "documents",
    ".odt": "documents", ".pptx": "documents", ".xlsx": "documents",
    ".xls": "documents", ".txt": "documents", ".csv": "documents",
    ".tsv": "documents",
    # archives — includes installers & disk images
    ".zip": "archives", ".rar": "archives", ".7z": "archives",
    ".tar": "archives", ".gz": "archives", ".tgz": "archives",
    ".zst": "archives",
    ".iso": "archives", ".img": "archives",
    ".exe": "archives", ".deb": "archives", ".msi": "archives",
    ".jar": "archives", ".appimage": "archives",
    # models
    ".pt": "models", ".pth": "models", ".h5": "models",
    ".pkl": "models", ".onnx": "models", ".safetensors": "models",
    # dev
    ".py": "dev", ".sh": "dev", ".js": "dev", ".ts": "dev",
    ".html": "dev", ".css": "dev", ".json": "dev", ".yaml": "dev",
    ".yml": "dev", ".toml": "dev", ".ipynb": "dev",
    ".plist": "dev", ".skill": "dev",
    ".woff": "dev", ".woff2": "dev", ".ttf": "dev", ".otf": "dev",
    # logs
    ".log": "logs", ".bak": "logs", ".part": "logs",
}

HOME_SKIP = {
    ".bashrc", ".bash_profile", ".bash_logout", ".bash_history",
    ".profile", ".zshrc", ".zprofile",
    ".claude.json", ".claude.json.backup",
    "README.md", "MEMORY.md",
    "package.json", "package-lock.json", "bun.lock",
}

# pkg.tar.zst is an Arch package installer (double extension)
def get_category(path: Path) -> str | None:
    name = path.name
    ext = path.suffix.lower()

    # Incomplete downloads → logs (quarantine)
    if name.endswith(".part"):
        return "logs"

    # Arch packages: name.pkg.tar.zst
    if name.endswith(".pkg.tar.zst"):
        return "archives"

    return EXT_MAP.get(ext)

def unique_dest(dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if not dest.exists():
        return dest
    stem, suffix = Path(name).stem, Path(name).suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem}({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def collect_moves(source_dir: Path, skip_names: set, dry_run: bool) -> list[dict]:
    moves = []
    for item in sorted(source_dir.iterdir(), key=lambda p: p.name.lower()):
        if item.name.startswith("."):
            continue
        if item.name in skip_names:
            continue
        if not item.is_file():
            continue

        cat = get_category(item)
        if cat is None:
            continue

        dest_dir = DEST[cat]
        if item.parent == dest_dir:
            continue

        dest_path = unique_dest(dest_dir, item.name)
        moves.append({"src": str(item), "dst": str(dest_path), "cat": cat})

        if dry_run:
            print(f"  [{cat:<9}]  {item.name}  →  {dest_path.relative_to(HOME)}")

    return moves

def run_moves(moves: list[dict]) -> None:
    for m in moves:
        dest = Path(m["dst"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(m["src"], m["dst"])
        print(f"  moved  {Path(m['src']).name}  →  {Path(m['dst']).relative_to(HOME)}")

    entry = {"timestamp": datetime.now().isoformat(), "moves": moves}
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists():
        log = json.loads(LOG_FILE.read_text())
        log["moves"].extend(moves)
        log["timestamp"] = entry["timestamp"]
    else:
        log = entry
    LOG_FILE.write_text(json.dumps(log, indent=2))
    print(f"\n✓ {len(moves)} files moved. Log → {LOG_FILE}")

def undo_moves() -> None:
    if not LOG_FILE.exists():
        print("No move log found.")
        return
    log = json.loads(LOG_FILE.read_text())
    moves = log["moves"]
    print(f"Undoing {len(moves)} moves from {log['timestamp']}\n")
    for m in reversed(moves):
        src, dst = Path(m["src"]), Path(m["dst"])
        if dst.exists():
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(src))
            print(f"  restored  {dst.name}")
        else:
            print(f"  SKIP (not found)  {dst.name}")
    LOG_FILE.unlink()
    print("\n✓ Undo complete.")

def process(source_dir: Path, skip: set, do_run: bool, label: str) -> None:
    if do_run:
        moves = collect_moves(source_dir, skip, dry_run=False)
        if not moves:
            print(f"({label}) Nothing to move.")
        else:
            print(f"Moving {len(moves)} files from {label}...\n")
            run_moves(moves)
    else:
        print(f"DRY RUN ({label}) — pass --run to apply.\n")
        moves = collect_moves(source_dir, skip, dry_run=True)
        if not moves:
            print("Nothing to organize.")
        else:
            print(f"\n{len(moves)} files would be moved.")

if __name__ == "__main__":
    args = set(sys.argv[1:])
    do_run = "--run" in args

    if "--undo" in args:
        undo_moves()
    elif "--all" in args:
        process(HOME, HOME_SKIP, do_run, "home")
        process(HOME / "Downloads", set(), do_run, "Downloads")
    elif "--downloads" in args:
        process(HOME / "Downloads", set(), do_run, "Downloads")
    else:
        process(HOME, HOME_SKIP, do_run, "home")
