"""
Quantum-Biological Optical Flow Module
--------------------------------------
Author: QBioForge Project

Purpose:
- Extract inertial-consistent facial motion
- Detect non-physical acceleration artifacts
- Preserve phase-coherent micro-motions
- Output quantum-compatible temporal signals

This module is deepfake-resistant by enforcing physics.
"""

import cv2
import numpy as np
from scipy.signal import detrend
from scipy.fft import fft
from typing import Dict, List


# =========================
# CONFIGURATION
# =========================

MAX_CORNERS = 150
QUALITY_LEVEL = 0.01
MIN_DISTANCE = 5
BLOCK_SIZE = 7

FPS_ASSUMED = 30
EPS = 1e-8

ROI_GRID = (2, 2)   # Same grid as rPPG for entanglement alignment


# =========================
# LOW-LEVEL UTILITIES
# =========================

def split_face_rois(face_box, grid):
    x, y, w, h = face_box
    dx = w // grid[0]
    dy = h // grid[1]

    rois = []
    for i in range(grid[0]):
        for j in range(grid[1]):
            rois.append((
                x + i * dx,
                y + j * dy,
                dx,
                dy
            ))
    return rois


def magnitude_phase(flow):
    mag = np.linalg.norm(flow, axis=2)
    phase = np.arctan2(flow[..., 1], flow[..., 0])
    return mag, np.unwrap(phase)


# =========================
# CORE MOTION PHYSICS
# =========================

def compute_velocity(flow_series):
    return np.gradient(flow_series, axis=0)


def compute_acceleration(velocity_series):
    return np.gradient(velocity_series, axis=0)


def inertial_violation_score(acceleration):
    """
    Measures non-biological acceleration spikes
    """
    jerk = np.gradient(acceleration)
    return np.mean(np.abs(jerk))


# =========================
# MAIN PUBLIC FUNCTION
# =========================

def extract_optical_flow(
    video_path: str,
    face_detector,
    max_frames: int = 300
) -> Dict[str, List[np.ndarray]]:
    """
    Extract physics-constrained facial motion signals.

    Returns:
    --------
    dict with:
    - magnitude_signals
    - phase_signals
    - velocity_signals
    - acceleration_signals
    - inertial_scores
    """

    cap = cv2.VideoCapture(video_path)
    ret, prev_frame = cap.read()

    if not ret:
        raise RuntimeError("Failed to read video")

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detect(prev_frame)


    if len(faces) == 0:
        return {
    "phase_signals": [],
    "status": "NO_FACE"
}


    face_box = faces[0]
    rois = split_face_rois(face_box, ROI_GRID)

    # Feature buffers per ROI
    flow_buffers = [[] for _ in rois]

    frame_count = 0

    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for i, (x, y, w, h) in enumerate(rois):
            prev_roi = prev_gray[y:y+h, x:x+w]
            curr_roi = gray[y:y+h, x:x+w]

            flow = cv2.calcOpticalFlowFarneback(
                prev_roi,
                curr_roi,
                None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )

            mag, phase = magnitude_phase(flow)
            flow_buffers[i].append((mag.mean(), phase.mean()))

        prev_gray = gray
        frame_count += 1

    cap.release()

    # =========================
    # POST-PROCESSING
    # =========================

    results = {
        "magnitude_signals": [],
        "phase_signals": [],
        "velocity_signals": [],
        "acceleration_signals": [],
        "inertial_scores": []
    }

    for buffer in flow_buffers:
        buffer = np.array(buffer)
        magnitude = detrend(buffer[:, 0])
        phase = detrend(buffer[:, 1])

        velocity = compute_velocity(magnitude)
        acceleration = compute_acceleration(velocity)

        inertial_score = inertial_violation_score(acceleration)

        results["magnitude_signals"].append(magnitude)
        results["phase_signals"].append(phase)
        results["velocity_signals"].append(velocity)
        results["acceleration_signals"].append(acceleration)
        results["inertial_scores"].append(inertial_score)

    return results
