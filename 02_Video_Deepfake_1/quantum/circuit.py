"""
Full Quantum Biological Circuit
-------------------------------
Author: QBioForge Project

Purpose:
- Assemble the complete quantum pipeline
- Encode biology into quantum states
- Apply biological Hamiltonian evolution
- Measure forensic quantum observables
- Expose density matrices for temporal analysis

This circuit is the quantum core of the detector.
"""

import pennylane as qml
import numpy as np
from typing import Dict, List

from quantum.encoding import (
    encode_biological_state,
    encode_mixed_biological_state
)
from quantum.hamiltonian import build_biological_hamiltonian
from quantum.evolution import evolve_biological_state
from quantum.measurements import (
    coherence_observables,
    entanglement_observables
)

EPS = 1e-9


# =========================
# DEVICE FACTORY
# =========================

def create_device(
    num_qubits: int,
    mixed: bool = True
):
    """
    Create a quantum device.
    default.mixed is required for density matrices.
    """
    dev_name = "default.mixed" if mixed else "default.qubit"
    return qml.device(dev_name, wires=num_qubits)


# =========================
# SINGLE-TIME-STEP CIRCUIT
# =========================

def build_quantum_circuit(
    num_qubits: int,
    mixed_state: bool = True
):
    """
    Returns a QNode that:
    - Encodes biological features
    - Evolves under biological Hamiltonian
    - Outputs observables + density matrix
    """

    dev = create_device(num_qubits, mixed=mixed_state)

    @qml.qnode(dev)
    def circuit(
        features: np.ndarray,
        time: float,
        heart_freq: float,
        coupling: float,
        inertia: float,
        optical: float
    ):
        # -------------------------
        # 1. Quantum State Encoding
        # -------------------------
        if mixed_state:
            encode_mixed_biological_state(
                features,
                num_qubits
            )
        else:
            encode_biological_state(
                features,
                num_qubits
            )

        # -------------------------
        # 2. Biological Hamiltonian
        # -------------------------
        H = build_biological_hamiltonian(
            num_qubits=num_qubits,
            heart_freq=heart_freq,
            coupling=coupling,
            inertia=inertia,
            optical=optical
        )

        # -------------------------
        # 3. Time Evolution
        # -------------------------
        evolve_biological_state(
            hamiltonian=H,
            num_qubits=num_qubits,
            time=time
        )

        # -------------------------
        # 4. Measurements
        # -------------------------
        wires = list(range(num_qubits))

        coherence = coherence_observables(wires)
        entanglement = entanglement_observables(wires)

        # Density matrix (full forensic access)
        rho = qml.density_matrix(wires=wires)

        return (*coherence, *entanglement, rho)

    return circuit


# =========================
# TEMPORAL EVOLUTION WRAPPER
# =========================

class QuantumBiologicalPipeline:
    """
    Executes the quantum circuit across time
    and stores full forensic state evolution.
    """

    def __init__(
        self,
        num_qubits: int,
        heart_freq: float = 1.2,
        coupling: float = 0.15,
        inertia: float = 0.08,
        optical: float = 0.05,
        mixed_state: bool = True
    ):
        self.num_qubits = num_qubits
        self.params = {
            "heart_freq": heart_freq,
            "coupling": coupling,
            "inertia": inertia,
            "optical": optical
        }
        self.circuit = build_quantum_circuit(
            num_qubits,
            mixed_state=mixed_state
        )

    def run(
        self,
        features: np.ndarray,
        timesteps: List[float]
    ) -> Dict[str, List]:
        """
        Run the quantum system across time.

        Returns:
        --------
        dict with:
        - coherence
        - entanglement
        - density_matrices
        """

        coherence_history = []
        entanglement_history = []
        density_matrices = []

        for t in timesteps:
            outputs = self.circuit(
                features,
                t,
                **self.params
            )

            num_coh = self.num_qubits
            num_ent = self.num_qubits - 1

            coherence = outputs[:num_coh]
            entanglement = outputs[num_coh:num_coh + num_ent]
            rho = outputs[-1]

            coherence_history.append(coherence)
            entanglement_history.append(entanglement)
            density_matrices.append(rho)

        return {
            "coherence": coherence_history,
            "entanglement": entanglement_history,
            "density_matrices": density_matrices
        }
