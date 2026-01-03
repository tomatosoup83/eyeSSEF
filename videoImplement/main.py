"""eyeSSEF pupil detection (video -> raw.csv)

This script:
- takes a pupil/eye video (.mp4) as input
- extracts frames to ./frames/
- runs PuReST (via pypupilext) per-frame to estimate pupil diameter + confidence
- writes a dataset folder to ./data/<video_basename>/ containing:
  - raw.csv
  - rawPlot.png
  - meta.json (fps, thresholds, etc.)
very important for me to understand ^

Original repo version had a hard-coded path. This version adds a CLI so it can be
used in an automated pipeline. yay
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
from pathlib import Path

import cv2
import pandas as pd

import scripts.detection.ppDetect as ppDetect
import scripts.others.graph as graph
import scripts.others.util as util

# -----------------
# Defaults (kept as module-level globals because other modules import these)
# -----------------

DEFAULT_CONFIDENCE_THRESH = 0.75
DEFAULT_PX_TO_MM = 30  # for 1080p in the team's calibration


def reset_folder(folder: Path) -> Path:
    """Delete folder if exists, then recreate empty."""
    if folder.exists():
        util.dprint(f"folder '{folder}' exists, removing contents in folder")
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def video_to_images(video: Path, frames_dir: Path) -> tuple[float, int]:
    """Extract all frames to frames_dir as BMPs. Returns (fps, total_frames)."""
    util.dprint(f"Trying to convert video '{video}' into frames and storing into '{frames_dir}'")

    cam = cv2.VideoCapture(str(video))
    if not cam.isOpened():
        raise RuntimeError(f"Could not open video: {video}")

    fps = cam.get(cv2.CAP_PROP_FPS)
    util.dprint(f"Video frame rate: {fps} fps")

    currentframe = 0
    while True:
        ret, frame = cam.read()
        if not ret:
            break
        out_path = frames_dir / f"frame{currentframe}.bmp"
        cv2.imwrite(str(out_path), frame)
        currentframe += 1

    cam.release()
    cv2.destroyAllWindows()
    util.dprint("All frames done!")

    return float(fps), int(currentframe)


def calculate_timestamps(fps: float, total_frames: int) -> list[float]:
    time_per_frame = 1.0 / float(fps)
    return [i * time_per_frame for i in range(total_frames)]


def pupil_detection_in_folder(
    frames_dir: Path,
    window_title: str,
    preview: bool,
) -> tuple[list[float], list[float]]:
    """Run pupil detection on frame0.bmp..frameN.bmp in frames_dir."""
    util.dprint(f"Starting pupil detection in folder '{frames_dir}'")

    files = sorted(frames_dir.glob("frame*.bmp"), key=lambda p: int(p.stem.replace("frame", "")))
    conf: list[float] = []
    diameter: list[float] = []

    for f in files:
        img_with_pupil, outline_confidence, pupil_diameter = ppDetect.detect(str(f))
        conf.append(float(outline_confidence))
        # pupil_diameter can be None depending on detection
        diameter.append(float(pupil_diameter) if pupil_diameter is not None else float('nan'))

        if preview:
            cv2.imshow(window_title, img_with_pupil)
            cv2.waitKey(1)

    if preview:
        cv2.destroyAllWindows()

    return conf, diameter


def save_data_to_csv(
    frame_ids: list[int],
    timestamps: list[float],
    diameters_px: list[float],
    confidences: list[float],
    output_path: Path,
    confidence_thresh: float,
    px_to_mm: float,
) -> pd.DataFrame:
    """Save dataframe with columns: frame_id, timestamp, diameter, diameter_mm, confidence, is_bad_data"""
    df = pd.DataFrame(
        {
            "frame_id": frame_ids,
            "timestamp": timestamps,
            "diameter": diameters_px,
            "confidence": confidences,
        }
    )
    df["is_bad_data"] = df["confidence"] < float(confidence_thresh)
    df["diameter_mm"] = df["diameter"] / float(px_to_mm)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    util.dprint(f"Data saved to CSV at '{output_path}'")
    return df


def generate_report(
    video_path: Path,
    out_root: Path,
    confidence_thresh: float = DEFAULT_CONFIDENCE_THRESH,
    px_to_mm: float = DEFAULT_PX_TO_MM,
    preview: bool = False,
    keep_frames: bool = False,
) -> Path:
    """Main pipeline. Returns the created dataset folder path."""

    util.dprint("Running pupil detection implementation...")

    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Working dirs (inside videoImplement)
    videos_dir = Path("videos")
    frames_dir = Path("frames")

    reset_folder(videos_dir)
    reset_folder(frames_dir)

    fps, total_frames = video_to_images(video_path, frames_dir)
    conf, diameters = pupil_detection_in_folder(frames_dir, window_title=f"Pupil Detection: {video_path.name}", preview=preview)

    timestamps = calculate_timestamps(fps, total_frames)

    session_name = video_path.stem
    dataset_dir = out_root / session_name
    dataset_dir.mkdir(parents=True, exist_ok=True)

    raw_csv = dataset_dir / "raw.csv"
    df = save_data_to_csv(
        frame_ids=list(range(total_frames)),
        timestamps=timestamps,
        diameters_px=diameters,
        confidences=conf,
        output_path=raw_csv,
        confidence_thresh=confidence_thresh,
        px_to_mm=px_to_mm,
    )

    # Save basic metadata so downstream steps don't need to guess fps
    meta = {
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "video_path": str(video_path),
        "video_name": video_path.name,
        "fps": fps,
        "total_frames": total_frames,
        "confidence_thresh": confidence_thresh,
        "px_to_mm": px_to_mm,
    }
    (dataset_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # Plot
    graph.plotResults(df, savePath=str(dataset_dir / "rawPlot.png"), showPlot=False, showMm=True)

    util.dprint(f"Finished raw extraction: {dataset_dir}")

    if not keep_frames:
        # Prevent frames directory from growing forever
        try:
            shutil.rmtree(frames_dir)
        except Exception:
            pass

    return dataset_dir


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run pupil detection on an eye video and write raw.csv")
    p.add_argument("--video", required=True, help="Path to eye video (.mp4)")
    p.add_argument("--out-root", default="data", help="Output root folder (default: ./data)")
    p.add_argument("--confidence-thresh", type=float, default=DEFAULT_CONFIDENCE_THRESH)
    p.add_argument("--px-to-mm", type=float, default=DEFAULT_PX_TO_MM)
    p.add_argument("--preview", action="store_true", help="Show OpenCV preview window during detection")
    p.add_argument("--keep-frames", action="store_true", help="Keep extracted frames on disk")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    video = Path(args.video).expanduser().resolve()

    # IMPORTANT: run from inside videoImplement folder so relative imports + paths work
    out_root = Path(args.out_root)

    generate_report(
        video_path=video,
        out_root=out_root,
        confidence_thresh=args.confidence_thresh,
        px_to_mm=args.px_to_mm,
        preview=args.preview,
        keep_frames=args.keep_frames,
    )
