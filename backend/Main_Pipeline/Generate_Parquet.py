#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate_Parquet.py
───────────────────
Extract Action-Unit features with OpenFace and save them
(in S3 column subset) to a Parquet file.

Called by Run_Pipeline.py:

    python Generate_Parquet.py \
        --openface  </path/to/FeatureExtraction> \
        --video     </path/to/video.mp4> \
        --output    </where/lstm_input.parquet> \
        [--fps 5] [--min_conf 0.7]
"""

import os, re, subprocess, tempfile, argparse
from pathlib import Path
from typing import List, Union

import pandas as pd

REGEX_S3  = r"^AU\d{2}_[rc]$"
LABEL_COL = "engagement_label"

# ────────────────────────── Helpers ────────────────────────── #
def downsample_video(video: str, fps: int) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_path = tmp.name
    tmp.close()
    subprocess.run(
        ["ffmpeg", "-y", "-i", video, "-vf", f"fps={fps}", "-loglevel", "error", tmp_path],
        check=True
    )
    return tmp_path


def run_openface_video(bin_path: str, video: str, out_dir: Path, fps: int) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ds_video = downsample_video(video, fps)
    subprocess.run([bin_path, "-f", ds_video, "-aus", "-out_dir", str(out_dir)], check=True)
    os.remove(ds_video)
    csvs = sorted(out_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not csvs:
        raise FileNotFoundError("OpenFace did not emit any CSV output.")
    return csvs[0]


def collect_openface_csvs(csv_files: Union[Path, List[Path]]) -> pd.DataFrame:
    csv_files = [csv_files] if isinstance(csv_files, Path) else csv_files
    dfs = [pd.read_csv(p) for p in csv_files]
    for df, p in zip(dfs, csv_files):
        df["source_csv"] = p.name
    return pd.concat(dfs, ignore_index=True)


def filter_to_s3(df: pd.DataFrame) -> pd.DataFrame:
    au_cols   = [c for c in df.columns if re.match(REGEX_S3, c)]
    meta_cols = [c for c in ("frame", "timestamp", "face_id", "source_csv") if c in df.columns]
    return df[meta_cols + au_cols] if meta_cols else df[au_cols]


def generate_parquet(openface_bin: str, video_path: str, out_path: str,
                     fps: int, min_conf: float) -> None:

    out_parquet = Path(out_path).expanduser().resolve()
    of_out_dir  = out_parquet.parent / "of_out"
    video_path  = Path(video_path).expanduser().resolve()

    csv_path = run_openface_video(openface_bin, str(video_path), of_out_dir, fps)
    df_raw   = collect_openface_csvs(csv_path)

    if "confidence" in df_raw.columns:
        df_raw = df_raw[df_raw["confidence"] >= min_conf].reset_index(drop=True)

    df_s3 = filter_to_s3(df_raw)
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    df_s3.to_parquet(out_parquet, index=False)
    print(f"✅ Saved Parquet → {out_parquet}")


# ────────────────────────── CLI entry ────────────────────────── #
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--openface", required=True, help="Path to OpenFace FeatureExtraction binary")
    ap.add_argument("--video",    required=True, help="Input video file")
    ap.add_argument("--output",   required=True, help="Destination .parquet file")
    ap.add_argument("--fps",      type=int, default=5, help="FPS for down-sampling (default 5)")
    ap.add_argument("--min_conf", type=float, default=0.7,
                    help="Discard frames with OpenFace confidence below this")
    args = ap.parse_args()

    generate_parquet(
        openface_bin = str(Path(args.openface).expanduser().resolve()),
        video_path   = str(Path(args.video).expanduser().resolve()),
        out_path     = str(Path(args.output).expanduser().resolve()),
        fps          = args.fps,
        min_conf     = args.min_conf,
    )
