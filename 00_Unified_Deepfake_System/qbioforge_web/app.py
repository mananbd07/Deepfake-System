import sys
import os
import uuid
import threading
import tempfile
import base64
import cv2
import numpy as np
import shutil
import traceback
import joblib

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

# ======================================================
# PROJECT ROOT PATH
# ======================================================

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# ======================================================
# ENGINES
# ======================================================

from experiments.run_single_video import run as quantum_run
from model.image_detector import analyze_image
from model.extract_features import extract_features

# ======================================================
# FLASK CONFIG
# ======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024 * 1024  # 2GB

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25
)

# Load Audio Model
try:
    audio_model = joblib.load(os.path.join(PROJECT_ROOT, "model", "audio_classifier.pkl"))
    audio_scaler = joblib.load(os.path.join(PROJECT_ROOT, "model", "scaler.pkl"))
except Exception as e:
    print(f"Warning: Could not load audio model: {e}")
    audio_model, audio_scaler = None, None

# ======================================================
# WEBSITE ROUTES
# ======================================================

@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/detect-video")
def detect_video():
    return render_template("detect_video.html")
    
@app.route("/detect-audio")
def detect_audio():
    return render_template("detect_audio.html")

@app.route("/detect-image")
def detect_image():
    return render_template("detect_image.html")

# ======================================================
# AUDIO UPLOAD & ANALYSIS API
# ======================================================

@app.route("/analyze-audio", methods=["POST"])
def analyze_audio():
    if "audio" not in request.files:
        return render_template("result.html", verdict="ERROR", confidence=0, message="No file selected", type="Audio")

    file = request.files["audio"]
    if file.filename == "":
        return render_template("result.html", verdict="ERROR", confidence=0, message="Empty filename", type="Audio")

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"{uuid.uuid4().hex}.flac")
    file.save(filepath)

    try:
        features = extract_features(filepath)
        if features is None or len(features) == 0:
            return render_template("result.html", verdict="ERROR", confidence=0, message="Could not process audio", type="Audio")

        X = audio_scaler.transform([features])
        probs = audio_model.predict_proba(X)[0]

        fake_prob = probs[1]
        real_prob = probs[0]

        verdict = "FAKE" if fake_prob > real_prob else "REAL"
        confidence = int(max(fake_prob, real_prob) * 100)

        return render_template("result.html", verdict=verdict, confidence=confidence, type="Audio")
    except Exception as e:
        return render_template("result.html", verdict="ERROR", confidence=0, message=str(e), type="Audio")

# ======================================================
# IMAGE UPLOAD & ANALYSIS API
# ======================================================

@app.route("/analyze-image", methods=["POST"])
def analyze_img():
    if "image" not in request.files:
        return render_template("result.html", verdict="ERROR", confidence=0, message="No file selected", type="Image")

    file = request.files["image"]
    if file.filename == "":
        return render_template("result.html", verdict="ERROR", confidence=0, message="Empty filename", type="Image")

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], f"{uuid.uuid4().hex}.jpg")
    file.save(filepath)

    try:
        result = analyze_image(filepath, app.config["UPLOAD_FOLDER"])
        return render_template("result.html", 
                               verdict=result["verdict"], 
                               confidence=result["confidence"], 
                               message=f"Anomaly Score: {result['metrics']['anomaly_score']:.2f}",
                               type="Image")
    except Exception as e:
        return render_template("result.html", verdict="ERROR", confidence=0, message=str(e), type="Image")

# ======================================================
# VIDEO UPLOAD & SOCKET API
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
        return jsonify({"error": "Upload failed"}), 500
    return jsonify({"path": save_path})

@socketio.on("start_analysis")
def start_analysis(data):
    video_path = data.get("path")
    if not video_path or not os.path.exists(video_path):
        socketio.emit("error", {"msg": "Invalid video path"})
        return
    worker = threading.Thread(target=run_web_pipeline, args=(video_path,), daemon=True)
    worker.start()

def run_web_pipeline(video_path):
    def progress_cb(percent, stage):
        socketio.emit("progress", {"value": int(percent), "stage": stage})
    try:
        socketio.emit("progress", {"value": 5, "stage": "Initializing quantum biological system"})
        result = quantum_run(video_path, progress_cb)
        if result is None:
            raise RuntimeError("Quantum engine returned empty result")
        
        # Determine verdict
        verdict = result.get("verdict", "UNKNOWN")
        confidence = int(result.get("confidence", 0) * 100)
        
        socketio.emit("completed", {
            "verdict": verdict,
            "confidence": confidence,
            "metrics": result.get("metrics", {}),
            "explanation": [] # Simplified for integration
        })
    except Exception as e:
        print("WEB PIPELINE ERROR:", str(e))
        traceback.print_exc()
        socketio.emit("error", {"msg": str(e)})

# ======================================================
# SERVER START
# ======================================================

if __name__ == "__main__":
    print("\n======================================")
    print("[+] UNIFIED DEEPFAKE PLATFORM ONLINE")
    print("======================================")
    print("[+] Web UI       : http://localhost:8080")
    print("======================================\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=8080,
        debug=False,
        allow_unsafe_werkzeug=True
    )

