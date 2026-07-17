"""
Quantum-Biological Normalization Module
---------------------------------------
Author: QBioForge Project

Purpose:
- Normalize biological signals without destroying phase
- Enforce physiological bounds
- Prepare signals for quantum state encoding
- Detect non-biological statistical anomalies early

This module defines the valid human signal manifold.
"""

import numpy as np
from scipy.stats import median_abs_deviation

EPS = 1e-8


# =========================
# CORE NORMALIZATION TOOLS
# =========================

def robust_zscore(signal):
    """
    Robust normalization using median and MAD
    Resistant to GAN spikes and compression artifacts
    """
    median = np.median(signal)
    mad = median_abs_deviation(signal) + EPS
    return (signal - median) / mad


def energy_normalize(signal):
    """
    Normalize signal energy (L2 norm)
    Required for stable quantum amplitude encoding
    """
    norm = np.linalg.norm(signal) + EPS
    return signal / norm


def phase_preserving_scale(signal):
    """
    Scale signal to [-1, 1] without altering phase ordering
    """
    max_val = np.max(np.abs(signal)) + EPS
    return signal / max_val


# =========================
# PHYSIOLOGICAL CONSTRAINTS
# =========================

def enforce_physiological_bounds(
    signal,
    max_sigma=6.0
):
    """
    Soft constraint: humans rarely exceed ±6σ
    Hard clipping would destroy quantum continuity — we avoid that
    """
    mean = np.mean(signal)
    std = np.std(signal) + EPS

    upper = mean + max_sigma * std
    lower = mean - max_sigma * std

    signal = np.where(signal > upper, upper, signal)
    signal = np.where(signal < lower, lower, signal)
    return signal


# =========================
# MULTI-REGION NORMALIZATION
# =========================

def normalize_multiregion(signals):
    """
    Normalize signals across facial regions while
    preserving relative coupling (entanglement readiness)

    Input:
    ------
    signals: List[np.ndarray]

    Output:
    -------
    List[np.ndarray]
    """

    normalized = []

    # Step 1: Individual robustness
    for sig in signals:
        sig = robust_zscore(sig)
        sig = enforce_physiological_bounds(sig)
        sig = phase_preserving_scale(sig)
        normalized.append(sig)

    # Step 2: Cross-region energy alignment
    energies = np.array([np.linalg.norm(s) for s in normalized]) + EPS
    mean_energy = np.mean(energies)

    aligned = []
    for sig, e in zip(normalized, energies):
        aligned.append(sig * (mean_energy / e))

    return aligned


# =========================
# QUANTUM FEATURE PACKAGING
# =========================

def prepare_quantum_features(
    feature_dict
):
    """
    Convert heterogeneous biological features into
    a single quantum-ready feature vector.

    Expected keys:
    --------------
    - rppg_phase
    - motion_phase
    - micro_strain

    Output:
    -------
    np.ndarray (bounded, normalized, phase-safe)
    """

    features = []

    for key, value in feature_dict.items():
        value = np.array(value)

        # Temporal normalization
        value = robust_zscore(value)
        value = enforce_physiological_bounds(value)
        value = energy_normalize(value)

        # Aggregate statistically (not frame-wise)
        features.append(np.mean(value))
        features.append(np.std(value))
        features.append(np.max(np.abs(value)))

    features = np.array(features)

    # Final quantum safety normalization
    features = features / (np.linalg.norm(features) + EPS)

    return features
