#!/usr/bin/env python3
"""
infer_AU_rf.py
---------------------------------------------
Run *S3 (Action-Unit only)* inference with the
Random-Forest/XGB model you trained on set-3.

Input  : Parquet containing ONLY the columns below
Output : preds_frames.csv  – per-frame predictions
         preds_video.csv   – one-row summary (mode label)
         lstm_input.npz    – contains X (and now Y arrays)

Usage (venv active)
    python infer_AU_rf.py            # ← uses hard-coded defaults
or
    python infer_AU_rf.py --parquet  /other/file.parquet \
                          --scaler   /other/scaler.joblib  \
                          --model    /other/model.joblib   \
                          --out_dir  /where/you/want
"""

from __future__ import annotations
import argparse, joblib, numpy as np, pandas as pd, re, sys
from pathlib import Path

# ───────────────────────  CONSTANTS  ──────────────────────── #
DEFAULT_PARQUET = Path(
    "/Users/kalyanrajavaram/Projects/GenerateNumbers/Student-Engagement/ML_models/trained_models/eval_features.parquet"
)
DEFAULT_SCALER  = Path(
    "/Users/kalyanrajavaram/Projects/GenerateNumbers/Student-Engagement/ML_models/trained_models/scaler_s3_AU.joblib"
)
DEFAULT_MODEL   = Path(
"/Users/kalyanrajavaram/Projects/GenerateNumbers/Student-Engagement/ML_models/trained_models/model_xgb_2.joblib"
)
DEFAULT_OUT_DIR = Path(
    "/Users/kalyanrajavaram/Projects/GenerateNumbers/Student-Engagement/ML_models/trained_models/results_rf"
)

# The exact S3 header you gave (order preserved)
AU_COLS = [
    "AU01_r","AU02_r","AU04_r","AU05_r","AU06_r","AU07_r","AU09_r","AU10_r",
    "AU12_r","AU14_r","AU15_r","AU17_r","AU20_r","AU23_r","AU25_r","AU26_r",
    "AU45_r","AU01_c","AU02_c","AU04_c","AU05_c","AU06_c","AU07_c","AU09_c",
    "AU10_c","AU12_c","AU14_c","AU15_c","AU17_c","AU20_c","AU23_c","AU25_c",
    "AU26_c","AU28_c","AU45_c"
]
META_COLS = ["frame", "face_id", "timestamp", "confidence", "success"]
REQUIRED = AU_COLS  # strictly required for scaling

# ───────────────────────  HELPERS  ────────────────────────── #
def align_and_scale(df: pd.DataFrame, scaler) -> np.ndarray:
    """Re-order columns, add missing =0, apply MinMaxScaler."""
    needed = list(scaler["feature_cols"]) if isinstance(scaler, dict) else AU_COLS
    for col in needed:
        if col not in df.columns:
            df[col] = 0.0
    X = scaler["scaler"].transform(df[needed])
    return X

def predict_per_frame(X: np.ndarray, model) -> pd.DataFrame:
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        pred  = proba.argmax(axis=1)
        conf  = proba.max(axis=1)
        out   = pd.DataFrame({"pred_label": pred, "pred_conf": conf})
        # attach each class prob p_<class>
        for idx in range(proba.shape[1]):
            out[f"p_{idx}"] = proba[:, idx]
    else:
        pred = model.predict(X)
        out  = pd.DataFrame({"pred_label": pred, "pred_conf": 1.0})
    return out

def summarize_video(per_frame: pd.DataFrame) -> pd.DataFrame:
    mode = per_frame["pred_label"].mode().iloc[0]
    conf = per_frame.loc[per_frame["pred_label"] == mode,"pred_conf"].mean()
    return pd.DataFrame([{"video_pred": int(mode), "video_conf": float(conf)}])

def sliding_windows(X: np.ndarray, window: int, stride: int) -> np.ndarray:
    """Creates sliding window sequences for LSTM input."""
    if window <= 0 or stride <= 0 or window > len(X):
        return np.empty((0,))
    return np.stack([X[i:i+window] for i in range(0, len(X) - window + 1, stride)])

# ───────────────────────  MAIN  ───────────────────────────── #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet",  default=DEFAULT_PARQUET)
    ap.add_argument("--scaler",   default=DEFAULT_SCALER)
    ap.add_argument("--model",    default=DEFAULT_MODEL)
    ap.add_argument("--out_dir",  default=DEFAULT_OUT_DIR)
    ap.add_argument("--min_conf", type=float, default=None,
                    help="Drop frames if OpenFace confidence < val (column must exist)")
    ap.add_argument("--window", type=int, default=0, help="Optional window size for LSTM prep")
    ap.add_argument("--stride", type=int, default=0, help="Optional stride for LSTM prep")
    args = ap.parse_args()

    parq   = Path(args.parquet).expanduser().resolve()
    scaler = joblib.load(Path(args.scaler).expanduser())
    model  = joblib.load(Path(args.model ).expanduser())
    outdir = Path(args.out_dir).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    # ── Load parquet ──────────────────────────────────────────
    df = pd.read_parquet(parq)

    # sanity-check
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        sys.exit(f"❌ AU columns missing in parquet: {missing[:10]} ...")

    # optional confidence filter
    if args.min_conf is not None and "confidence" in df.columns:
        df = df[df["confidence"] >= args.min_conf].reset_index(drop=True)

    # Separate meta / AU
    df_meta = df[[c for c in META_COLS if c in df.columns]].copy()
    X       = align_and_scale(df[AU_COLS].copy(), scaler)

    # ── Predict ───────────────────────────────────────────────
    per_frame = predict_per_frame(X, model)
    # re-attach meta
    for col in df_meta.columns:
        per_frame[col] = df_meta[col].values

    # ── Build Y arrays from per_frame (to store in NPZ) ───────
    proba_cols = sorted(
        [c for c in per_frame.columns if re.match(r"^p_\d+$", c)],
        key=lambda s: int(s.split("_")[1])
    )
    y_label = per_frame["pred_label"].to_numpy(dtype=np.int32)
    y_conf  = per_frame["pred_conf"].to_numpy(dtype=float) if "pred_conf" in per_frame else np.array([])
    y_proba = per_frame[proba_cols].to_numpy(dtype=float) if proba_cols else np.empty((len(per_frame), 0))

    # ── Write outputs ─────────────────────────────────────────
    per_frame.to_csv(outdir / "preds_frames.csv", index=False)
    summarize_video(per_frame).to_csv(outdir / "preds_video.csv", index=False)

    # ── Save sliding-window LSTM input if requested ──────────
    if args.window > 0 and args.stride > 0:
        X_seq = sliding_windows(X, args.window, args.stride)
        np.savez(outdir / "lstm_input.npz",
                 X=X_seq,
                 y_frame_label=y_label,
                 y_frame_conf=y_conf,
                 y_frame_proba=y_proba)
        print("🧠 Saved LSTM-ready input →", outdir / "lstm_input.npz")
    else:
        # still provide per-frame Y alongside X (no windowing)
        np.savez(outdir / "lstm_input.npz",
                 X=X,
                 y_frame_label=y_label,
                 y_frame_conf=y_conf,
                 y_frame_proba=y_proba)
        print("🧠 Saved per-frame NPZ (no windowing) →", outdir / "lstm_input.npz")

    print("✅  Finished inference")
    print("Frames  →", outdir / "preds_frames.csv")
    print("Video   →", outdir / "preds_video.csv")

if __name__ == "__main__":
    main()
