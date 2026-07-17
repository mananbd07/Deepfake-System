"""
Quantum Forensic Detector (Calibrated)
-------------------------------------
Author: QBioForge Project

Purpose:
- Use calibrated biological ranges (real-only)
- Decide REAL vs DEEPFAKE using physics-based constraints
- Provide explainable forensic evidence

This detector does NOT learn.
It enforces biological reality.
"""

import json
import os
import numpy as np
from typing import Dict, List

from quantum.measurements import (
    von_neumann_entropy,
    purity,
    state_fidelity,
    quantum_sensitivity
)

EPS = 1e-9


# =========================
# LOAD CALIBRATED THRESHOLDS
# =========================

DEFAULT_CALIBRATION_PATH = os.path.join(
    os.path.dirname(__file__),
    "calibrated_thresholds.json"
)


def load_calibrated_thresholds(path=DEFAULT_CALIBRATION_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Calibrated thresholds not found at {path}. "
            "Run calibrate_real_videos.py first."
        )

    with open(path, "r") as f:
        return json.load(f)


CALIBRATED = load_calibrated_thresholds()


# =========================
# HELPER: RANGE CHECK
# =========================

def in_biological_range(value, stats, tolerance=0.10):
    """
    Check if value lies within calibrated biological range
    with tolerance (to avoid hard cutoffs).

    tolerance = 10% soft margin
    """
    low = stats["robust_min"]
    high = stats["robust_max"]

    span = high - low
    low -= tolerance * span
    high += tolerance * span

    return low <= value <= high


# =========================
# METRIC EXTRACTION
# =========================

def compute_temporal_fidelities(
    density_matrices: List[np.ndarray]
) -> List[float]:
    fidelities = []
    for i in range(len(density_matrices) - 1):
        f = state_fidelity(
            density_matrices[i],
            density_matrices[i + 1]
        )
        fidelities.append(f)
    return fidelities


def summarize_quantum_metrics(
    quantum_trace: Dict[str, List]
) -> Dict[str, float]:

    coherence_vals = np.abs(
        np.array(quantum_trace["coherence"])
    ).mean(axis=1)

    entanglement_vals = (
        np.abs(np.array(quantum_trace["entanglement"]))
        .mean(axis=1)
        if quantum_trace["entanglement"] else
        np.zeros_like(coherence_vals)
    )

    density_matrices = quantum_trace["density_matrices"]

    entropies = [
        von_neumann_entropy(rho)
        for rho in density_matrices
    ]

    purities = [
        purity(rho)
        for rho in density_matrices
    ]

    fidelities = compute_temporal_fidelities(
        density_matrices
    )

    sensitivity = quantum_sensitivity(
        np.array(coherence_vals)
    )

    return {
        "coherence_mean": float(np.mean(coherence_vals)),
        "entanglement_mean": float(np.mean(entanglement_vals)),
        "entropy_mean": float(np.mean(entropies)),
        "purity_mean": float(np.mean(purities)),
        "fidelity_mean": float(np.mean(fidelities)),
        "sensitivity": float(sensitivity)
    }


# =========================
# CALIBRATED DECISION ENGINE
# =========================

class QuantumDeepfakeDetector:
    """
    Calibrated, physics-based deepfake detector.
    """

    def __init__(self):
        self.calibration = CALIBRATED

    def evaluate(
        self,
        quantum_trace: Dict[str, List]
    ) -> Dict[str, float]:
        return summarize_quantum_metrics(quantum_trace)

    def decide(
        self,
        metrics: Dict[str, float]
    ) -> Dict[str, object]:

        violations = []

        for metric_name, value in metrics.items():
            if metric_name not in self.calibration:
                continue

            stats = self.calibration[metric_name]
            if not in_biological_range(value, stats):
                violations.append(metric_name.upper())

        # Decision rule:
        # Humans may violate 1 metric due to noise
        # Deepfakes violate multiple constraints
        verdict = (
            "DEEPFAKE"
            if len(violations) >= 2
            else "REAL"
        )

        confidence = min(
            1.0,
            len(violations) / max(len(self.calibration), 1)
        )

        return {
            "verdict": verdict,
            "confidence": confidence,
            "violations": violations,
            "metrics": metrics
        }
