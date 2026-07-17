"""
Biological Quantum Hamiltonian
------------------------------
Author: QBioForge Project

Purpose:
- Define physically valid human facial dynamics
- Enforce biological rhythm, coupling, and inertia
- Penalize non-human temporal evolution
- Serve as the core of quantum time evolution

This Hamiltonian defines what "human" means.
"""

import pennylane as qml
import numpy as np
from typing import List


# =========================
# DEFAULT BIOLOGICAL CONSTANTS
# =========================

DEFAULT_HEART_FREQ = 1.2       # Hz (≈72 BPM)
DEFAULT_COUPLING = 0.15        # Neuromuscular coupling
DEFAULT_INERTIA = 0.08         # Motion resistance
DEFAULT_OPTICAL = 0.05         # Skin reflectance stability
DEFAULT_DECOHERENCE = 0.02     # Biological noise

EPS = 1e-9


# =========================
# HAMILTONIAN COMPONENTS
# =========================

def heartbeat_hamiltonian(
    wires: List[int],
    heart_freq: float = DEFAULT_HEART_FREQ
):
    """
    Periodic cardiovascular rhythm
    """
    coeffs, ops = [], []

    for w in wires:
        coeffs.append(2 * np.pi * heart_freq)
        ops.append(qml.PauliZ(w))

    return coeffs, ops


def neuromuscular_coupling(
    wires: List[int],
    coupling: float = DEFAULT_COUPLING
):
    """
    Sparse local muscle coupling
    """
    coeffs, ops = [], []

    for i in range(len(wires) - 1):
        coeffs.append(coupling)
        ops.append(qml.PauliX(wires[i]) @ qml.PauliX(wires[i + 1]))

    return coeffs, ops


def mechanical_inertia(
    wires: List[int],
    inertia: float = DEFAULT_INERTIA
):
    """
    Penalizes rapid state changes (non-biological acceleration)
    """
    coeffs, ops = [], []

    for w in wires:
        coeffs.append(inertia)
        ops.append(qml.PauliY(w))

    return coeffs, ops


def optical_energy_constraint(
    wires: List[int],
    strength: float = DEFAULT_OPTICAL
):
    """
    Enforces smooth skin reflectance dynamics
    """
    coeffs, ops = [], []

    for w in wires:
        coeffs.append(strength)
        ops.append(qml.PauliX(w))

    return coeffs, ops


# =========================
# FULL BIOLOGICAL HAMILTONIAN
# =========================

def build_biological_hamiltonian(
    num_qubits: int,
    heart_freq: float = DEFAULT_HEART_FREQ,
    coupling: float = DEFAULT_COUPLING,
    inertia: float = DEFAULT_INERTIA,
    optical: float = DEFAULT_OPTICAL
) -> qml.Hamiltonian:
    """
    Construct the complete biological Hamiltonian.

    H = H_heart + H_coupling + H_inertia + H_optical
    """

    wires = list(range(num_qubits))

    coeffs: List[float] = []
    ops: List[qml.operation.Operator] = []

    for builder in [
        lambda: heartbeat_hamiltonian(wires, heart_freq),
        lambda: neuromuscular_coupling(wires, coupling),
        lambda: mechanical_inertia(wires, inertia),
        lambda: optical_energy_constraint(wires, optical)
    ]:
        c, o = builder()
        coeffs.extend(c)
        ops.extend(o)

    return qml.Hamiltonian(coeffs, ops)


# =========================
# BIOLOGICAL VALIDITY CHECK
# =========================

def validate_biological_parameters(
    heart_freq: float,
    coupling: float,
    inertia: float,
    optical: float
):
    """
    Prevents non-human parameter regimes.
    """
    if not (0.6 <= heart_freq <= 3.5):
        raise ValueError("Heart frequency outside human range")

    if not (0.05 <= coupling <= 0.3):
        raise ValueError("Unrealistic neuromuscular coupling")

    if not (0.01 <= inertia <= 0.2):
        raise ValueError("Non-biological motion inertia")

    if not (0.01 <= optical <= 0.1):
        raise ValueError("Optical stability violation")
