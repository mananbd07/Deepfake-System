"""
Quantum Measurement & Forensic Metrics Module
---------------------------------------------
Author: QBioForge Project

Purpose:
- Measure biologically meaningful quantum observables
- Quantify coherence, entanglement, and entropy
- Detect non-human temporal evolution
- Provide explainable forensic signals

This module answers:
"What does the quantum system reveal about reality?"
"""

import pennylane as qml
import numpy as np
from typing import Dict, List

EPS = 1e-9


# =========================
# BASIC OBSERVABLES
# =========================

def coherence_observables(wires: List[int]):
    """
    Measures local phase coherence.
    """
    return [qml.expval(qml.PauliX(w)) for w in wires]


def entanglement_observables(wires: List[int]):
    """
    Measures pairwise correlations between facial regions.
    """
    observables = []
    for i in range(len(wires) - 1):
        observables.append(
            qml.expval(
                qml.PauliX(wires[i]) @ qml.PauliX(wires[i + 1])
            )
        )
    return observables


# =========================
# DENSITY MATRIX METRICS
# =========================

def von_neumann_entropy(rho: np.ndarray) -> float:
    """
    Computes S(ρ) = -Tr(ρ log ρ)
    """
    eigvals = np.linalg.eigvalsh(rho)
    eigvals = eigvals[eigvals > EPS]
    return -np.sum(eigvals * np.log(eigvals))


def purity(rho: np.ndarray) -> float:
    """
    Tr(ρ²) — humans are neither pure nor maximally mixed
    """
    return np.real(np.trace(rho @ rho))


# =========================
# TEMPORAL CONSISTENCY
# =========================

def state_fidelity(
    rho_t: np.ndarray,
    rho_t1: np.ndarray
) -> float:
    """
    Uhlmann fidelity between consecutive states.
    """
    sqrt_rho = scipy_sqrtm(rho_t)
    product = sqrt_rho @ rho_t1 @ sqrt_rho
    return np.real(np.trace(scipy_sqrtm(product))) ** 2


def scipy_sqrtm(matrix: np.ndarray) -> np.ndarray:
    """
    Stable matrix square root using eigen decomposition.
    """
    eigvals, eigvecs = np.linalg.eigh(matrix)
    eigvals = np.maximum(eigvals, 0)
    return eigvecs @ np.diag(np.sqrt(eigvals)) @ eigvecs.T.conj()


# =========================
# QUANTUM SENSITIVITY
# =========================

def quantum_sensitivity(observations: np.ndarray) -> float:
    """
    Measures how unstable the system is to small perturbations.

    Deepfakes often show hyper-sensitivity due to
    latent-space over-optimization.
    """
    diffs = np.diff(observations)
    return np.mean(np.abs(diffs))


# =========================
# AGGREGATION INTERFACE
# =========================

def aggregate_measurements(
    coherence: List[float],
    entanglement: List[float],
    entropy: float,
    purity_value: float,
    fidelity: float,
    sensitivity: float
) -> Dict[str, float]:
    """
    Package all forensic signals into a single dictionary.
    """
    return {
        "coherence_mean": float(np.mean(np.abs(coherence))),
        "entanglement_mean": float(np.mean(np.abs(entanglement)))
            if entanglement else 0.0,
        "entropy": float(entropy),
        "purity": float(purity_value),
        "fidelity": float(fidelity),
        "sensitivity": float(sensitivity)
    }
