# routes.py
import os, tempfile, subprocess, json
from flask import Blueprint, request, jsonify
from app import db
from models import PomodoroSession

bp = Blueprint("api", __name__)

# ✨ EDIT THIS to your actual path:
RUN_PIPELINE = "/absolute/path/to/Main_Pipeline/Run_Pipeline.py"

@bp.route("/upload", methods=["POST"])
def upload():
    try:
        user_id = int(request.headers.get("X-User-Id", "1"))
        task = request.form.get("task") or None
        task_category = request.form.get("task_category") or None

        file = request.files.get("video")
        if not file:
            return jsonify({"error": "No file"}), 400

        # Per-request working dir
        run_dir = tempfile.mkdtemp(prefix="pom-")
        webm_path = os.path.join(run_dir, "session.webm")
        mp4_path  = os.path.join(run_dir, "session.mp4")

        # Save upload
        file.save(webm_path)

        # Convert to mp4
        ff = subprocess.run(
            ["ffmpeg", "-y", "-i", webm_path, "-c:v", "libx264", "-preset", "fast", mp4_path],
            capture_output=True, text=True
        )
        if ff.returncode != 0:
            return jsonify({"error": "ffmpeg failed", "stderr": ff.stderr[-400:]}), 500

        # 🔁 Run the full pipeline in a unique out_dir; it prints ONLY JSON
        out_dir = tempfile.mkdtemp(prefix="pom-out-")
        proc = subprocess.run(
            ["python", RUN_PIPELINE, "--out_dir", out_dir, mp4_path],
            capture_output=True, text=True
        )
        if proc.returncode != 0:
            return jsonify({"error": "pipeline failed", "stderr": proc.stderr[-400:]}), 500

        # Parse analyzer JSON
        pipeline_result = json.loads(proc.stdout.strip())

        # Persist
        summary    = pipeline_result.get("summary") or {}
        segments   = pipeline_result.get("segments") or []
        series_1hz = pipeline_result.get("series_1hz") or []

        sess = PomodoroSession(
            user_id=user_id,
            task=task,
            task_category=task_category,
            focus_score=summary.get("mean_focus_score"),
            summary_json=summary,
            segments_json=segments,
            series_1hz=series_1hz,
            video_path=mp4_path,         # keep temp or move to permanent storage first
            # you can also store out_dir if you want to inspect artifacts later
        )
        db.session.add(sess)
        db.session.commit()

        return jsonify({"session_id": sess.id, "pipeline_result": pipeline_result}), 200

    except Exception as e:
        # Always return JSON to keep the frontend happy
        return jsonify({"error": str(e)}), 500
