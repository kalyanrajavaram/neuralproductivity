# Run_Pipeline.py (replace the config block + main with this shape)

import argparse
import subprocess
import sys
from pathlib import Path

def die(msg: str, code: int = 1):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(code)

def run(cmd: list[str], step_name: str, check_stdout=False):
    """Run a subprocess; if check_stdout True, return CompletedProcess."""
    print(f"{step_name}", file=sys.stderr)
    return subprocess.run(cmd, text=True, capture_output=check_stdout, check=not check_stdout)

def run_pipeline(video: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    venv_py = out_dir.parent.parent / "venv" / "bin" / "python"   # adjust if needed

    generate_parquet = Path(__file__).parent / "Generate_Parquet.py"
    infer_au         = Path(__file__).parent / "Infer_Au.py"
    analyze_lstm     = Path(__file__).parent / "Analyze_Lstm.py"

    openface_bin = "/Users/kalyanrajavaram/Downloads/OpenFace/build/bin/FeatureExtraction"
    scaler_path  = Path(__file__).parent / "scaler_s3_AU.joblib"
    model_path   = Path(__file__).parent / "model_xgb_2.joblib"

    parquet_path = out_dir / "lstm_input.parquet"
    npz_path     = out_dir / "lstm_input.npz"

    # Clean old artifacts if they exist in this out_dir
    for p in (parquet_path, npz_path):
        try: p.unlink()
        except FileNotFoundError: pass

    # 1) Parquet
    run(
        [str(venv_py), str(generate_parquet),
         "--openface", openface_bin, "--video", str(video), "--output", str(parquet_path)],
        "[1/3] Generating AU features → Parquet"
    )
    if not parquet_path.exists():
        die(f"Parquet not found: {parquet_path}")

    # 2) AU inference → NPZ
    run(
        [str(venv_py), str(infer_au),
         "--parquet", str(parquet_path), "--scaler", str(scaler_path),
         "--model", str(model_path), "--out_dir", str(out_dir)],
        "[2/3] Running AU inference"
    )
    if not npz_path.exists():
        die(f"NPZ not found: {npz_path}")

    # 3) Analyze (capture JSON and print ONLY JSON to stdout)
    cp = subprocess.run(
        [str(venv_py), str(analyze_lstm),
         "--npz", str(npz_path), "--video", str(video), "--out_dir", str(out_dir)],
        text=True, capture_output=True
    )
    if cp.returncode != 0:
        print(cp.stderr[-500:], file=sys.stderr)
        die("Analyze_Lstm.py failed")

    # IMPORTANT: emit ONLY the analyzer JSON to stdout
    print(cp.stdout.strip())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run full AU + LSTM engagement pipeline")
    ap.add_argument("--out_dir", required=True, help="Output directory (unique per run)")
    ap.add_argument("video", help="Absolute path to the input video file")
    args = ap.parse_args()

    video_path = Path(args.video).expanduser().resolve()
    if not video_path.exists():
        die(f"Video file not found: {video_path}")
    out_dir = Path(args.out_dir).expanduser().resolve()
    run_pipeline(video=video_path, out_dir=out_dir)
