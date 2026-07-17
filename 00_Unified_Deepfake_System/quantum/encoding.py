"""
Quantum State Encoding Module
-----------------------------
Author: QBioForge Project

Purpose:
- Encode biological signals into quantum states
- Preserve amplitude (energy) and phase (timing)
- Seed entanglement for facial subsystems
- Remain stable on NISQ hardware

This file defines how "biology becomes quantum".
"""

import pennylane as qml
import numpy as np
from typing import Sequence

EPS = 1e-9


# =========================
# VALIDATION
# =========================

def validate_features(features: np.ndarray, num_qubits: int):
    """
    Ensure features are quantum-safe
    """
    if not isinstance(features, np.ndarray):
        raise TypeError("Features must be numpy array")

    if features.ndim != 1:
        raise ValueError("Features must be 1D")

    if len(features) > 2 ** num_qubits:
        raise ValueError(
            f"Too many features ({len(features)}) "
            f"for {num_qubits} qubits"
        )

    norm = np.linalg.norm(features)
    if not np.isclose(norm, 1.0, atol=1e-3):
        raise ValueError(
            f"Features must be L2-normalized (norm={norm})"
        )


# =========================
# AMPLITUDE ENCODING
# =========================

def amplitude_encode(features: np.ndarray, wires: Sequence[int]):
    """
    Amplitude encoding with automatic quantum-safe padding.

    Quantum requirement:
    len(features) == 2 ** len(wires)
    """

    num_qubits = len(wires)
    target_len = 2 ** num_qubits
    current_len = len(features)

    if current_len > target_len:
        raise ValueError(
            f"Feature length {current_len} exceeds "
            f"quantum capacity {target_len}"
        )

    if current_len < target_len:
        # Biologically safe padding:
        # pad with very small energy, not zeros
        pad_size = target_len - current_len
        pad_value = np.mean(np.abs(features)) * 1e-3
        padding = np.full(pad_size, pad_value)
        features = np.concatenate([features, padding])

        # Re-normalize to unit norm
        features = features / (np.linalg.norm(features) + 1e-12)

    qml.AmplitudeEmbedding(
        features,
        wires=wires,
        normalize=False
    )



# =========================
# PHASE ENCODING
# =========================

def phase_encode(features: np.ndarray, wires: Sequence[int]):
    """
    Encodes physiological phase using Z-rotations.
    Small rotations → micro-timing sensitivity.
    """
    for i, w in enumerate(wires):
        phase = np.arcsin(
            np.clip(features[i], -1 + EPS, 1 - EPS)
        )
        qml.RZ(2.0 * phase, wires=w)


# =========================
# BIOLOGICAL ENTANGLEMENT SEEDING
# =========================

def seed_biological_entanglement(
    wires: Sequence[int],
    coupling_strength: float = 0.3
):
    """
    Seed weak, biologically plausible entanglement.
    Avoids over-entanglement (non-human).
    """
    for i in range(len(wires) - 1):
        qml.IsingXX(
            coupling_strength,
            wires=[wires[i], wires[i + 1]]
        )


# =========================
# FULL ENCODING PIPELINE
# =========================

def encode_biological_state(
    features: np.ndarray,
    num_qubits: int,
    entangle: bool = True
):
    """
    Complete biological → quantum encoding pipeline.

    Steps:
    ------
    1. Validate features
    2. Amplitude encode (energy)
    3. Phase encode (timing)
    4. Seed entanglement (coupling)

    This function is meant to be called INSIDE a QNode.
    """

    validate_features(features, num_qubits)

    wires = list(range(num_qubits))

    # Step 1: Energy distribution
    amplitude_encode(features, wires)

    # Step 2: Temporal phase
    phase_encode(features, wires)

    # Step 3: Biological coupling
    if entangle and num_qubits > 1:
        seed_biological_entanglement(wires)


# =========================
# DENSITY MATRIX SAFE VARIANT
# =========================

def encode_mixed_biological_state(
    features: np.ndarray,
    num_qubits: int,
    noise_strength: float = 0.01
):
    """
    Encoding variant that explicitly models biological decoherence.
    Recommended for real hardware.
    """
    encode_biological_state(features, num_qubits)

    for w in range(num_qubits):
        qml.DepolarizingChannel(
            noise_strength,
            wires=w
        )
