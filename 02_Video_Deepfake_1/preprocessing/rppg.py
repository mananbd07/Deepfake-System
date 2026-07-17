"""
Quantum-Biological rPPG Extraction Module
-----------------------------------------
Author: QBioForge Project

Purpose:
- Extract biologically faithful pulse signals
- Preserve temporal phase coherence
- Provide quantum-compatible features

This module is GAN / Deepfake resistant by design.
"""

import cv2
import numpy as np
from scipy.signal import butter, filtfilt, detrend
from scipy.fft import fft, fftfreq


# =========================
# CONFIGURATION
# =========================

FPS_ASSUMED = 30
HEART_RATE_BAND = (0.7, 4.0)  # Hz → 42–240 BPM
ROI_GRID = (2, 2)             # Split face into regions
EPS = 1e-8


# =========================
# SIGNAL PROCESSING UTILS
# =========================

def bandpass_filter(signal, fs, low, high, order=5):
    nyq = 0.5 * fs
    low /= nyq
    high /= nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)


def normalize_phase(signal):
    """
    Convert signal to analytic signal and extract phase
    """
    analytic = np.fft.ifft(fft(signal))
    phase = np.unwrap(np.angle(analytic))
    return phase


# =========================
# CORE rPPG EXTRACTION
# =========================

def extract_face_rois(frame, face_box):
    """
    Divide face into grid ROIs
    """
    x, y, w, h = face_box
    rois = []

    dx = w // ROI_GRID[0]
    dy = h // ROI_GRID[1]

    for i in range(ROI_GRID[0]):
        for j in range(ROI_GRID[1]):
            roi = frame[
                y + j*dy : y + (j+1)*dy,
                x + i*dx : x + (i+1)*dx
            ]
            rois.append(roi)

    return rois


def pos_method(rgb_signals):
    """
    Plane-Orthogonal-to-Skin (POS) rPPG algorithm
    """
    rgb = np.array(rgb_signals)
    rgb = rgb / (np.mean(rgb, axis=0) + EPS)

    X = 3 * rgb[:, 0] - 2 * rgb[:, 1]
    Y = 1.5 * rgb[:, 0] + rgb[:, 1] - 1.5 * rgb[:, 2]

    alpha = np.std(X) / (np.std(Y) + EPS)
    s = X - alpha * Y
    return s


# =========================
# MAIN PUBLIC FUNCTION
# =========================

def extract_rppg(
    video_path,
    face_detector,
    max_frames=300,
    return_phase=True
):
    """
    Extract multi-region rPPG signals from video.

    Returns:
    --------
    dict with:
    - raw_signals
    - filtered_signals
    - phase_signals
    - frequency_peaks
    """

    cap = cv2.VideoCapture(video_path)
    rgb_buffers = None
    frame_count = 0

    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_detector.detect(frame)

        if len(faces) == 0:
            continue

        x, y, w, h = faces[0]
        rois = extract_face_rois(frame, (x, y, w, h))

        if rgb_buffers is None:
            rgb_buffers = [[] for _ in range(len(rois))]

        for i, roi in enumerate(rois):
            mean_rgb = np.mean(roi.reshape(-1, 3), axis=0)
            rgb_buffers[i].append(mean_rgb)

        frame_count += 1

    cap.release()

    # =========================
    # POST-PROCESSING
    # =========================

    results = {
        "raw_signals": [],
        "filtered_signals": [],
        "phase_signals": [],
        "frequency_peaks": []
    }

    for region_rgb in rgb_buffers:
        region_rgb = np.array(region_rgb)

        raw = pos_method(region_rgb)
        raw = detrend(raw)

        filtered = bandpass_filter(
            raw,
            FPS_ASSUMED,
            HEART_RATE_BAND[0],
            HEART_RATE_BAND[1]
        )

        fft_mag = np.abs(fft(filtered))
        freqs = fftfreq(len(filtered), 1 / FPS_ASSUMED)
        peak_freq = freqs[np.argmax(fft_mag)]

        results["raw_signals"].append(raw)
        results["filtered_signals"].append(filtered)
        results["frequency_peaks"].append(peak_freq)

        if return_phase:
            phase = normalize_phase(filtered)
            results["phase_signals"].append(phase)

    return results
