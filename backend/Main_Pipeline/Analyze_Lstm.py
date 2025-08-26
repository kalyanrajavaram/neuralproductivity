#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze_Lstm.py — continuous focus score
----------------------------------------
Uses y_frame_proba (p_0 p_1 p_2) from lstm_input.npz and the video FPS
to emit per-frame focus scores + a session summary.
"""

import argparse, numpy as np, pandas as pd
from pathlib import Path
import cv2

# ==============  Parameters you can tune  ==============
FOCUSED_CLASS = 2          # which column is "focused"
HALF_LIFE_S   = 1.0        # EMA half-life  (s)
TH_FOCUSED    = 0.75       # score ≥ → “Focused”
TH_PARTIAL    = 0.40       # score ≥ → “Partially focused”
# =======================================================

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
    α = 1 - np.exp(-np.log(2) / (half_life_s*fps))
    out, acc = np.empty_like(x, float), 0.0
    for i,v in enumerate(x.astype(float)):
        acc = α*v + (1-α)*(acc if i else v)
        out[i] = acc
    return out

def longest_streak(mask: np.ndarray) -> int:
    best = cur = 0
    for v in mask:
        cur = cur+1 if v else 0
        best = max(best, cur)
    return best
# ---------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz",   required=True, type=Path)
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--out_dir", required=True, type=Path)
    args = ap.parse_args()

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- load data ---
    data = np.load(args.npz)
    P = data["y_frame_proba"]            # (N,3)
    N  = P.shape[0]
    fps = get_fps(args.video)

    # --- compute continuous focus score ---
    p_focus_raw   = P[:, FOCUSED_CLASS]
    score         = ema(p_focus_raw, HALF_LIFE_S, fps)   # 0-1
    bucket        = np.where(score >= TH_FOCUSED,  "focused",
                     np.where(score >= TH_PARTIAL, "partial", "unfocused"))

    # --- framewise CSV (keep raw probs) ---
    df_frames = pd.DataFrame({
        "frame_idx": np.arange(N),
        "p_0": P[:,0], "p_1": P[:,1], "p_2": P[:,2],
        "focus_score": score,
        "focus_bucket": bucket
    })
    df_frames.to_csv(out_dir / "focus_framewise.csv", index=False)

    # --- session summary ---
    bucket_pct = (
        pd.Series(bucket).value_counts(normalize=True)
        .reindex(["focused","partial","unfocused"], fill_value=0)
        .mul(100)
    )
    longest_s = longest_streak(bucket == "focused")/fps
    pd.DataFrame([{
        "mean_focus_score": round(score.mean(),3),
        "pct_focused":      round(bucket_pct["focused"],1),
        "pct_partial":      round(bucket_pct["partial"],1),
        "pct_unfocused":    round(bucket_pct["unfocused"],1),
        "longest_focused_streak_s": round(longest_s,1)
    }]).to_csv(out_dir / "focus_summary.csv", index=False)

    # --- optionally still compute hard segments -------------
    # (same hysteresis code you had; keeps backward compatibility)
    ENTER_TH, EXIT_TH = TH_FOCUSED, TH_PARTIAL           # reuse thresholds
    state=False; locked=np.zeros(N,bool)
    for i,v in enumerate(score):
        if not state and v>=ENTER_TH: state=True
        elif state and v<=EXIT_TH:   state=False
        locked[i]=state
    segments=[]
    i=0
    while i<N:
        if locked[i]:
            j=i
            while j<N and locked[j]: j+=1
            segments.append((i/fps,(j-1)/fps,(j-i)/fps,i,j-1))
            i=j
        else: i+=1
    if segments:
        pd.DataFrame(segments,
            columns=["start_s","end_s","duration_s","start_frame","end_frame"]
        ).to_csv(out_dir / "focus_segments.csv", index=False)

    print(f"✅ Focus analysis complete → {out_dir}")

if __name__ == "__main__":
    main()
