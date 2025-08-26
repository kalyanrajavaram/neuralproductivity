#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run_Pipeline.py
───────────────
Entry-point for the complete video–engagement pipeline.

Order:
  1. Generate_Parquet.py  → AU features (.parquet)
  2. Infer_Au.py          → AU inference  (.npz)
  3. Analyze_Lstm.py      → Focus smoothing + CSVs

Outputs are written to backend/Main_Pipeline/results_rf/
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ────────────────────────── CONFIG ────────────────────────── #
BASE_DIR   = Path(__file__).resolve().parent           # …/Main_Pipeline
VENV_PY    = BASE_DIR.parent / "venv" / "bin" / "python"

GENERATE_PARQUET = BASE_DIR / "Generate_Parquet.py"
INFER_AU         = BASE_DIR / "Infer_Au.py"
ANALYZE_LSTM     = BASE_DIR / "Analyze_Lstm.py"

OUTPUT_DIR   = BASE_DIR / "results_rf"                 # one folder for all outputs
PARQUET_PATH = OUTPUT_DIR / "lstm_input.parquet"
NPZ_PATH     = OUTPUT_DIR / "lstm_input.npz"

OPENFACE_BIN = "/Users/kalyanrajavaram/Downloads/OpenFace/build/bin/FeatureExtraction"



SCALER_PATH  = BASE_DIR / "scaler_s3_AU.joblib"
MODEL_PATH   = BASE_DIR / "model_xgb_2.joblib"
# ──────────────────────────────────────────────────────────── #

def die(msg: str, code: int = 1):
    print(f"❌ {msg}")
    sys.exit(code)


def run(cmd: list[str], step_name: str):
    """Run a subprocess, abort on failure with a clear message."""
    print(f"🔹 {step_name}")
    result = subprocess.run(cmd, text=True)
    if result.returncode != 0:
        die(f"{step_name} failed (exit={result.returncode})")


def run_pipeline(video: Path):
    # Make sure output folder exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. ───────────────────────── Generate AU parquet ───────────────────────── #
    run(
        [
            str(VENV_PY),
            str(GENERATE_PARQUET),
            "--openface", OPENFACE_BIN,
            "--video",    str(video),
            "--output",   str(PARQUET_PATH)
        ],
        "[1/3] Generating AU features → Parquet"
    )
    if not PARQUET_PATH.exists():
        die(f"Parquet not found after Step 1: {PARQUET_PATH}")

    # 2. ─────────────────────────── Run AU inference ───────────────────────── #
    run(
        [
            str(VENV_PY),
            str(INFER_AU),
            "--parquet", str(PARQUET_PATH),
            "--scaler",  str(SCALER_PATH),
            "--model",   str(MODEL_PATH),
            "--out_dir", str(OUTPUT_DIR)
        ],
        "[2/3] Running AU inference"
    )
    if not NPZ_PATH.exists():
        die(f"NPZ not found after Step 2: {NPZ_PATH}")

    # 3. ─────────────────── LSTM-based focus smoothing ─────────────────────── #
    run(
        [
            str(VENV_PY),
            str(ANALYZE_LSTM),
            "--npz",    str(NPZ_PATH),
            "--video",  str(video),
            "--out_dir", str(OUTPUT_DIR)
        ],
        "[3/3] Analyzing engagement (LSTM)"
    )

    # ───────────────────────────── Summary ────────────────────────────── #
    print("\n✅ Pipeline finished successfully")
    print(f"   • Parquet  → {PARQUET_PATH}")
    print(f"   • NPZ      → {NPZ_PATH}")
    print(f"   • Results  → {OUTPUT_DIR}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run full AU + LSTM engagement pipeline")
    ap.add_argument("video", help="Absolute path to the input video file")
    args = ap.parse_args()

    video_path = Path(args.video).expanduser().resolve()
    if not video_path.exists():
        die(f"Video file not found: {video_path}")
    run_pipeline(video_path)
