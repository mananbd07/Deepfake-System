import os
import sys
import uuid
import threading
import tempfile
import base64
import shutil
import traceback

import cv2
import numpy as np

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# ======================================================
# PATH SETUP
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = BASE_DIR
sys.path.insert(0, PROJECT_ROOT)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ======================================================
# IMPORT YOUR ENGINE
# ======================================================

from experiments.run_single_video import run as quantum_run

# ======================================================
# FLASK APP
# ======================================================

app = Flask(__name__, template_folder="templates")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2GB

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# ======================================================
# ROUTES
# ======================================================

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/detect")
def detect():
    return render_template("index.html")

@app.route("/architecture")
def architecture():
    return render_template("architecture.html")

@app.route("/result")
def result():
    return render_template("result.html")

# ======================================================
# VIDEO UPLOAD
# ======================================================

@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files["video"]
    filename = f"{uuid.uuid4().hex}.mp4"
    save_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"path": save_path})

# ======================================================
# SOCKETIO ANALYSIS
# ======================================================

@socketio.on("start_analysis")
def start_analysis(data):
    video_path = data.get("path")

    if not video_path or not os.path.exists(video_path):
        socketio.emit("error", {"msg": "Invalid video path"})
        return

    thread = threading.Thread(
        target=run_pipeline,
        args=(video_path,),
        daemon=True
    )
    thread.start()

def run_pipeline(video_path):

    def progress_cb(percent, stage):
        socketio.emit("progress", {
            "value": int(percent),
            "stage": stage
        })

    try:
        socketio.emit("progress", {
            "value": 5,
            "stage": "Initializing quantum biological system"
        })

        result = quantum_run(video_path, progress_cb)

        if result is None:
            raise RuntimeError("Quantum engine returned empty result")

        explanation = generate_explanation(result)

        socketio.emit("completed", {
            "verdict": result.get("verdict", "UNKNOWN"),
            "confidence": int(result.get("confidence", 0) * 100),
            "metrics": result.get("metrics", {}),
            "explanation": explanation
        })

    except Exception as e:
        traceback.print_exc()
        socketio.emit("error", {"msg": str(e)})

# ======================================================
# FRAME → VIDEO (EXTENSION SUPPORT)
# ======================================================

def frames_to_video(frames, out_path, fps=5):
    first = cv2.imread(frames[0])
    h, w, _ = first.shape

    writer = cv2.VideoWriter(
        out_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h)
    )

    for f in frames:
        img = cv2.imread(f)
        if img is not None:
            writer.write(img)

    writer.release()

@app.route("/api/frame_scan", methods=["POST"])
def frame_scan():
    payload = request.get_json()
    frames = payload.get("frames", [])

    if len(frames) < 6:
        return jsonify({"error": "Too few frames"}), 400

    temp_dir = tempfile.mkdtemp(prefix="qbioforge_")
    saved = []

    try:
        for i, frame in enumerate(frames):
            header, encoded = frame.split(",", 1)
            img = cv2.imdecode(
                np.frombuffer(base64.b64decode(encoded), np.uint8),
                cv2.IMREAD_COLOR
            )
            path = os.path.join(temp_dir, f"{i}.jpg")
            cv2.imwrite(path, img)
            saved.append(path)

        video_path = os.path.join(temp_dir, "input.mp4")
        frames_to_video(saved, video_path)

        result = quantum_run(video_path)
        explanation = generate_explanation(result)

        return jsonify({
            "verdict": result.get("verdict"),
            "confidence": result.get("confidence"),
            "reason": " | ".join(explanation)
        })

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ======================================================
# EXPLANATION ENGINE
# ======================================================

def generate_explanation(result):
    metrics = result.get("metrics", {})
    reasons = []

    if metrics.get("coherence_mean", 1) < 0.06:
        reasons.append("Low biological quantum coherence")
    if metrics.get("entropy_mean", 0) > 0.30:
        reasons.append("High entropy generative texture")
    if metrics.get("purity_mean", 1) < 0.90:
        reasons.append("Non-human quantum purity profile")
    if metrics.get("sensitivity", 0) > 0.05:
        reasons.append("Temporal motion instability detected")

    if not reasons:
        reasons.append("Authentic human biological signature verified")

    return reasons

# ======================================================
# SERVER START (🔥 THIS IS THE IMPORTANT PART 🔥)
# ======================================================

if __name__ == "__main__":
    print("⚛️ QBIOFORGE ONLINE")

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        allow_unsafe_werkzeug=True   # ← REQUIRED FOR COLAB
    )
