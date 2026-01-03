"""Preprocess one dataset folder produced by main.py.

Input:  <data_dir>/raw.csv (and optionally <data_dir>/meta.json)
Output: <data_dir>/processed.csv + processedPlot.png

This is a generalized version of process.py, which in the original repo was hard-coded
to a sample dataset path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.others.util import dprint
import scripts.others.graph as graph

from scripts.preProcessing.firstPass import confidenceFilter
from scripts.preProcessing.secondPass import removeSusBio
from scripts.preProcessing.thirdPass import madFilter
from scripts.preProcessing.fourthPassCubicOnly import interpolateData
from scripts.preProcessing.sixthPass import savgolSmoothing


def _load_fps(data_dir: Path, fallback_fps: float) -> float:
    meta = data_dir / "meta.json"
    if meta.exists():
        try:
            obj = json.loads(meta.read_text(encoding="utf-8"))
            fps = float(obj.get("fps", fallback_fps))
            return fps
        except Exception:
            pass
    return float(fallback_fps)


def do_processing(df: pd.DataFrame, fps: float) -> pd.DataFrame:
    # 1) confidence filter
    df = confidenceFilter(df)

    # 2) biologically implausible
    df = removeSusBio(df, fps)

    # 3) MAD outlier filter
    df = madFilter(df)

    # 4) interpolate missing points
    df = interpolateData(df)

    # 5) smooth
    df = savgolSmoothing(df, fps=fps)

    return df


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Preprocess one dataset folder (raw.csv -> processed.csv)")
    p.add_argument("--data-dir", required=True, help="Dataset folder that contains raw.csv")
    p.add_argument("--fps", type=float, default=30.0, help="Fallback fps if meta.json is missing")
    p.add_argument("--plot", action="store_true", help="Show plot window")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    data_dir = Path(args.data_dir).expanduser().resolve()

    raw_csv = data_dir / "raw.csv"
    if not raw_csv.exists():
        raise FileNotFoundError(f"raw.csv not found in: {data_dir}")

    fps = _load_fps(data_dir, args.fps)
    dprint(f"Processing dataset: {data_dir.name} (fps={fps})")

    df = pd.read_csv(raw_csv)
    df_processed = do_processing(df, fps=fps)

    out_csv = data_dir / "processed.csv"
    df_processed.to_csv(out_csv, index=False)
    dprint(f"Processed data saved: {out_csv}")

    graph.plotResults(df_processed, savePath=str(data_dir / "processedPlot.png"), showPlot=args.plot, showMm=True)
