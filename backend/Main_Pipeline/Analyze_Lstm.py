#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze_Lstm.py — continuous focus score (CSV + JSON)
-----------------------------------------------------
Reads y_frame_proba (p_0 p_1 p_2) from lstm_input.npz and the video FPS.
Emits:
  - focus_framewise.csv
  - focus_summary.csv
  - focus_segments.csv (if any)
And prints a single JSON object to stdout combining paths + key data.
"""

import argparse, json, numpy as np, pandas as pd
from pathlib import Path
import cv2
import math

# ==============  Tunables  ==============
FOCUSED_CLASS = 2          # which column is "focused"
HALF_LIFE_S   = 1.0        # EMA half-life  (s)
TH_FOCUSED    = 0.75       # score ≥ → “Focused”
TH_PARTIAL    = 0.40       # score ≥ → “Partially focused”
DOWNSAMPLE_S  = 1.0        # include 1 Hz downsampled series in JSON (set 0 to skip)
# =======================================

# ---------- helpers ----------
def get_fps(video: Path) -> float:
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    if fps <= 0:
        raise RuntimeError(f"Could not read FPS from {video}")
    return fps

def ema(x: np.ndarray, half_life_s: float, fps: float) -> np.ndarray:
    if half_life_s <= 0: return x.astype(float, copy=True)
    alpha = 1 - math.exp(-math.log(2) / (half_life_s * fps))
    out, acc = np.empty_like(x, float), 0.0
    for i, v in enumerate(x.astype(float)):
        acc = alpha * v + (1 - alpha) * (acc if i else v)
        out[i] = acc
    return out

def longest_streak(mask: np.ndarray) -> int:
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best

def downsample_series(score: np.ndarray, bucket: np.ndarray, fps: float, step_s: float):
    if step_s <= 0: return []
    step = max(1, int(round(step_s * fps)))
    out = []
    for i in range(0, len(score), step):
        t_s = i / fps
        out.append({
            "t_s": round(t_s, 3),
            "score": float(score[i]),
            "bucket": str(bucket[i])
        })
    return out

# ---------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", required=True, type=Path)
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--out_dir", required=True, type=Path)
    args = ap.parse_args()

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- load data ---
    data = np.load(args.npz)
    P = data["y_frame_proba"]            # (N,3)
    N = P.shape[0]
    fps = get_fps(args.video)

    # --- compute continuous focus score ---
    p_focus_raw = P[:, FOCUSED_CLASS]
    score = ema(p_focus_raw, HALF_LIFE_S, fps)   # 0-1
    bucket = np.where(score >= TH_FOCUSED, "focused",
             np.where(score >= TH_PARTIAL, "partial", "unfocused"))

    # --- framewise CSV (keep raw probs) ---
    df_frames = pd.DataFrame({
        "frame_idx": np.arange(N),
        "p_0": P[:,0], "p_1": P[:,1], "p_2": P[:,2],
        "focus_score": score,
        "focus_bucket": bucket
    })
    framewise_csv = out_dir / "focus_framewise.csv"
    df_frames.to_csv(framewise_csv, index=False)

    # --- session summary ---
    bucket_pct = (
        pd.Series(bucket).value_counts(normalize=True)
        .reindex(["focused","partial","unfocused"], fill_value=0)
        .mul(100.0)
    )
    longest_s = longest_streak(bucket == "focused") / fps
    summary_dict = {
        "mean_focus_score": round(float(score.mean()), 3),
        "pct_focused":      round(float(bucket_pct["focused"]), 1),
        "pct_partial":      round(float(bucket_pct["partial"]), 1),
        "pct_unfocused":    round(float(bucket_pct["unfocused"]), 1),
        "longest_focused_streak_s": round(float(longest_s), 1)
    }
    summary_csv = out_dir / "focus_summary.csv"
    pd.DataFrame([summary_dict]).to_csv(summary_csv, index=False)

    # --- hysteresis-based segments (optional, for compatibility) ---
    ENTER_TH, EXIT_TH = TH_FOCUSED, TH_PARTIAL
    state = False
    locked = np.zeros(N, bool)
    for i, v in enumerate(score):
        if not state and v >= ENTER_TH: state = True
        elif state and v <= EXIT_TH:    state = False
        locked[i] = state

    segments = []
    i = 0
    while i < N:
        if locked[i]:
            j = i
            while j < N and locked[j]: j += 1
            segments.append({
                "start_s": i / fps,
                "end_s": (j - 1) / fps,
                "duration_s": (j - i) / fps,
                "start_frame": i,
                "end_frame": j - 1
            })
            i = j
        else:
            i += 1

    segments_csv = out_dir / "focus_segments.csv"
    if segments:
        pd.DataFrame(segments).to_csv(segments_csv, index=False)
    else:
        segments_csv = None  # nothing produced

    # --- optional downsampled timeseries for UI (1 Hz default) ---
    series_1hz = downsample_series(score, bucket, fps, DOWNSAMPLE_S)

    # --- combined JSON payload for backend/Flask ---
    payload = {
        "video": str(args.video.resolve()),
        "npz": str(args.npz.resolve()),
        "out_dir": str(out_dir),
        "fps": float(fps),
        "n_frames": int(N),
        "thresholds": {
            "focused": TH_FOCUSED,
            "partial": TH_PARTIAL,
            "ema_half_life_s": HALF_LIFE_S
        },
        "summary": summary_dict,
        "segments": segments,                      # [] if none
        "csv_paths": {
            "framewise": str(framewise_csv),
            "summary": str(summary_csv),
            "segments": str(segments_csv) if segments_csv else None
        },
        "series_1hz": series_1hz                  # small, UI-friendly
    }

    # Print JSON for Flask to capture
    print(json.dumps(payload))

if __name__ == "__main__":
    main()
