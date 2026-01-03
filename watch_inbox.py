"""Watch an inbox folder for new .mp4 files and automatically run the pipeline.

Why:
- You run the algorithm on the laptop (not on the Pi)
- The Pi drops .mp4 recordings into the inbox (via scp/Syncthing/SMB etc.)
- We process one file at a time (simple, avoids folder collisions)

This script calls:
  videoImplement/main.py       -> creates data/<session>/raw.csv + meta.json
  videoImplement/process_one.py -> creates data/<session>/processed.csv
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi"}


def wait_until_stable(path: Path, stable_for_s: float = 3.0, timeout_s: float = 600.0) -> bool:
    """Wait until file size doesn't change for `stable_for_s` seconds."""
    start = time.time()
    last_size = -1
    stable_since = None

    while True:
        if not path.exists():
            return False

        try:
            size = path.stat().st_size
        except OSError:
            size = -1

        now = time.time()

        if size == last_size and size > 0:
            if stable_since is None:
                stable_since = now
            elif (now - stable_since) >= stable_for_s:
                # Extra check: can we open it for reading?
                try:
                    with open(path, "rb"):
                        return True
                except OSError:
                    pass
        else:
            stable_since = None
            last_size = size

        if (now - start) > timeout_s:
            return False

        time.sleep(0.5)


def run_pipeline(python_exe: Path, repo_dir: Path, video_path: Path, out_root: Path) -> None:
    """Run main.py then process_one.py."""
    vi_dir = repo_dir / "videoImplement"

    # 1) raw extraction
    subprocess.run(
        [
            str(python_exe),
            "main.py",
            "--video",
            str(video_path),
            "--out-root",
            str(out_root),
        ],
        cwd=str(vi_dir),
        check=True,
    )

    # Data folder name is video basename
    data_dir = (vi_dir / out_root / video_path.stem).resolve()

    # 2) preprocessing
    subprocess.run(
        [
            str(python_exe),
            "process_one.py",
            "--data-dir",
            str(data_dir),
        ],
        cwd=str(vi_dir),
        check=True,
    )


class Handler(FileSystemEventHandler):
    def __init__(self, cfg):
        self.cfg = cfg
        self._busy = False

    def _maybe_process(self, path: Path):
        if self._busy:
            return
        if path.suffix.lower() not in VIDEO_EXTS:
            return

        self._busy = True
        try:
            print(f"[watch] detected: {path}")
            ok = wait_until_stable(path)
            if not ok:
                print(f"[watch] file never stabilized, skipping: {path}")
                return

            # Optional: move into a 'processing' folder to avoid duplicate triggers
            processing_dir = self.cfg.processing
            processing_dir.mkdir(parents=True, exist_ok=True)
            moved_path = processing_dir / path.name
            try:
                shutil.move(str(path), str(moved_path))
                path = moved_path
            except Exception:
                # If move fails (e.g. permissions), just process in place
                pass

            print(f"[watch] running pipeline on: {path}")
            run_pipeline(self.cfg.python, self.cfg.repo, path, self.cfg.out_root)
            print(f"[watch] done: {path}")

            # Archive
            if self.cfg.archive is not None:
                self.cfg.archive.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(self.cfg.archive / path.name))

        except subprocess.CalledProcessError as e:
            print(f"[watch] pipeline failed: {e}")
        finally:
            self._busy = False

    def on_created(self, event):
        if event.is_directory:
            return
        self._maybe_process(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory:
            return
        self._maybe_process(Path(event.dest_path))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--inbox", required=True, help="Folder where videos arrive")
    p.add_argument("--repo", required=True, help="Path to eyeSSEF-main repo")
    p.add_argument("--python", default=None, help="Python executable (default: current)")
    p.add_argument("--out-root", default="data", help="Output root under videoImplement (default: data)")
    p.add_argument("--processing", default=None, help="Move incoming files here before processing")
    p.add_argument("--archive", default=None, help="Move processed files here")
    return p.parse_args()


def main():
    args = parse_args()

    class Cfg:
        pass

    cfg = Cfg()
    cfg.inbox = Path(args.inbox).expanduser().resolve()
    cfg.repo = Path(args.repo).expanduser().resolve()
    cfg.out_root = Path(args.out_root)
    cfg.python = Path(args.python).expanduser().resolve() if args.python else Path(os.sys.executable)
    cfg.processing = Path(args.processing).expanduser().resolve() if args.processing else (cfg.inbox / "_processing")
    cfg.archive = Path(args.archive).expanduser().resolve() if args.archive else (cfg.inbox / "_archive")

    if not cfg.inbox.exists():
        raise FileNotFoundError(f"Inbox folder does not exist: {cfg.inbox}")

    print(f"[watch] inbox: {cfg.inbox}")
    print(f"[watch] repo:  {cfg.repo}")

    event_handler = Handler(cfg)
    observer = Observer()
    observer.schedule(event_handler, str(cfg.inbox), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
