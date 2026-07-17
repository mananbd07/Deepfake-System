"""
Quantum-Biological Micro-Expression Analysis Module
---------------------------------------------------
Author: QBioForge Project

Purpose:
- Detect neuromuscular micro-expression signals
- Preserve intent-level temporal structure
- Identify non-biological expression synthesis
- Output quantum-entanglement-ready features

This module targets the weakest point of deepfakes:
neuromuscular coordination.
"""

import cv2
import numpy as np
from scipy.signal import detrend, find_peaks
from scipy.stats import entropy
from typing import Dict, List


# =========================
# CONFIGURATION
# =========================

FPS_ASSUMED = 30
MICRO_EXPR_MAX_DURATION = 0.5  # seconds
MICRO_EXPR_FRAMES = int(FPS_ASSUMED * MICRO_EXPR_MAX_DURATION)

ROI_GRID = (2, 2)   # Must match rPPG & optical flow
EPS = 1e-8


# =========================
# UTILITIES
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


def compute_strain(prev_roi, curr_roi):
    """
    Measures subtle pixel-wise deformation (strain energy proxy)
    """
    diff = curr_roi.astype(np.float32) - prev_roi.astype(np.float32)
    return np.mean(np.abs(diff))


def sliding_window_energy(signal, window):
    energies = []
    for i in range(len(signal) - window):
        energies.append(np.sum(signal[i:i+window]**2))
    return np.array(energies)


# =========================
# NEUROMUSCULAR ANALYSIS
# =========================

def detect_micro_bursts(signal):
    """
    Detect short-duration energy bursts characteristic of micro-expressions
    """
    energy = sliding_window_energy(signal, MICRO_EXPR_FRAMES)
    energy = energy / (np.max(energy) + EPS)

    peaks, _ = find_peaks(
        energy,
        height=np.mean(energy) + np.std(energy),
        distance=MICRO_EXPR_FRAMES // 2
    )

    return energy, peaks


def coupling_entropy(signals):
    """
    Measures coordination between facial regions
    Low entropy → coordinated muscles
    High entropy → synthetic / decoupled motion
    """
    stacked = np.vstack(signals)
    covariance = np.cov(stacked)
    eigvals = np.linalg.eigvalsh(covariance)
    eigvals = eigvals[eigvals > EPS]
    eigvals = eigvals / np.sum(eigvals)
    return entropy(eigvals)


# =========================
# MAIN PUBLIC FUNCTION
# =========================

def extract_micro_expressions(
    video_path: str,
    face_detector,
    max_frames: int = 300
) -> Dict[str, List[np.ndarray]]:
    """
    Extract neuromuscular micro-expression signals.

    Returns:
    --------
    dict with:
    - strain_signals
    - burst_energies
    - burst_peaks
    - coupling_entropy
    """

    cap = cv2.VideoCapture(video_path)
    ret, prev_frame = cap.read()

    if not ret:
        raise RuntimeError("Failed to read video")

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detect(prev_frame)


    if len(faces) == 0:
        return {
    "strain_signals": [],
    "status": "NO_FACE"
}


    face_box = faces[0]
    rois = split_face_rois(face_box, ROI_GRID)

    # Per-ROI strain buffers
    strain_buffers = [[] for _ in rois]

    frame_count = 0

    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for i, (x, y, w, h) in enumerate(rois):
            prev_roi = prev_gray[y:y+h, x:x+w]
            curr_roi = gray[y:y+h, x:x+w]

            strain = compute_strain(prev_roi, curr_roi)
            strain_buffers[i].append(strain)

        prev_gray = gray
        frame_count += 1

    cap.release()

    # =========================
    # POST-PROCESSING
    # =========================

    results = {
        "strain_signals": [],
        "burst_energies": [],
        "burst_peaks": [],
        "coupling_entropy": None
    }

    processed_signals = []

    for strain in strain_buffers:
        strain = np.array(strain)
        strain = detrend(strain)
        strain = strain / (np.std(strain) + EPS)

        energy, peaks = detect_micro_bursts(strain)

        results["strain_signals"].append(strain)
        results["burst_energies"].append(energy)
        results["burst_peaks"].append(peaks)

        processed_signals.append(strain)

    # Cross-region neuromuscular coordination
    results["coupling_entropy"] = coupling_entropy(processed_signals)

    return results
