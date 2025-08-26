import os, uuid, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔧 Drop files directly into this folder
SAVE_DIR = "/Users/kalyanrajavaram/Projects/TodoList/backend/Main_Pipeline"

# (Optional) simple size limit ~500 MB
MAX_BYTES = 500 * 1024 * 1024

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("video")
    if not f:
        return jsonify({"error": "no 'video' file field in form-data"}), 400

    os.makedirs(SAVE_DIR, exist_ok=True)

    # Use a safe, unique base name (ignore client filename)
    base = str(uuid.uuid4())
    # Save the raw upload exactly as received (often .webm from MediaRecorder)
    src_path = os.path.join(SAVE_DIR, f"{base}.webm")
    mp4_path = os.path.join(SAVE_DIR, f"{base}.mp4")

    # Save upload
    f.save(src_path)

    # Basic size guard
    if os.path.getsize(src_path) > MAX_BYTES:
        try:
            os.remove(src_path)
        finally:
            return jsonify({"error": "file too large"}), 413

    # Convert to MP4 (x264)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", src_path,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-movflags", "+faststart",  # better for playback
                mp4_path
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        return jsonify({"error": "ffmpeg conversion failed"}), 500

    # (Optional) remove source after successful conversion
    try:
        os.remove(src_path)
    except OSError:
        pass

    return jsonify({
        "status": "success",
        "saved_mp4": mp4_path,
        "filename": os.path.basename(mp4_path)
    }), 200

if __name__ == "__main__":
    # Run on :8000 to match your frontend
    app.run(host="0.0.0.0", port=8000, debug=True)
