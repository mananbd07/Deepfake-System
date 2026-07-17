"""
Real-Only Quantum Calibration Script (MediaPipe)
------------------------------------------------
Calibrates biological quantum metrics using ONLY real videos.
"""

import os
import json
import argparse
import numpy as np
from tqdm import tqdm

# =========================
# PREPROCESSING
# =========================
from preprocessing.rppg import extract_rppg
from preprocessing.optical_flow import extract_optical_flow
from preprocessing.micro_expression import extract_micro_expressions
from preprocessing.normalize import prepare_quantum_features
from preprocessing.face_detector import MediaPipeFaceDetector

# =========================
# QUANTUM CORE
# =========================
from quantum.circuit import QuantumBiologicalPipeline
from model.detector import QuantumDeepfakeDetector


# =========================
# ROBUST STATISTICS
# =========================

def robust_range(values, k=3.0):
    values = np.array(values)
    median = np.median(values)
    mad = np.median(np.abs(values - median)) + 1e-9
    return float(median - k * mad), float(median + k * mad)


def percentile_range(values, low=5, high=95):
    values = np.array(values)
    return float(np.percentile(values, low)), float(np.percentile(values, high))


# =========================
# MAIN CALIBRATION LOGIC
# =========================

def calibrate(real_video_dir: str, output_path: str):
    face_detector = MediaPipeFaceDetector()
    detector = QuantumDeepfakeDetector()

    metric_bank = {
        "coherence_mean": [],
        "entanglement_mean": [],
        "entropy_mean": [],
        "purity_mean": [],
        "fidelity_mean": [],
        "sensitivity": []
    }

    videos = [
        os.path.join(real_video_dir, f)
        for f in os.listdir(real_video_dir)
        if f.lower().endswith((".mp4", ".avi", ".mov"))
    ]

    if len(videos) < 5:
        raise RuntimeError("Calibration requires at least 5 real videos.")

    print(f"\n⚛️ Calibrating using {len(videos)} REAL videos\n")

    for video_path in tqdm(videos, desc="Calibrating"):
        try:
            rppg = extract_rppg(video_path, face_detector)
            flow = extract_optical_flow(video_path, face_detector)
            micro = extract_micro_expressions(video_path, face_detector)

            feature_dict = {}

            if rppg.get("phase_signals"):
                feature_dict["rppg_phase"] = np.concatenate(rppg["phase_signals"])

            if flow.get("phase_signals"):
                feature_dict["motion_phase"] = np.concatenate(flow["phase_signals"])

            if micro.get("strain_signals"):
                feature_dict["micro_strain"] = np.concatenate(micro["strain_signals"])

            if not feature_dict:
                continue

            quantum_features = prepare_quantum_features(feature_dict)

            num_qubits = int(np.ceil(np.log2(len(quantum_features))))
            quantum_features = quantum_features[: 2 ** num_qubits]

            pipeline = QuantumBiologicalPipeline(num_qubits=num_qubits)
            timesteps = np.linspace(0.05, 1.0, 6).tolist()

            quantum_trace = pipeline.run(quantum_features, timesteps)
            metrics = detector.evaluate(quantum_trace)

            for k in metric_bank:
                metric_bank[k].append(metrics[k])

        except Exception as e:
            print(f"⚠️ Skipping {video_path}: {e}")

    calibrated = {}

    for metric, values in metric_bank.items():
        if not values:
            continue

        r_min, r_max = robust_range(values)
        p_min, p_max = percentile_range(values)

        calibrated[metric] = {
            "robust_min": r_min,
            "robust_max": r_max,
            "percentile_5": p_min,
            "percentile_95": p_max,
            "median": float(np.median(values))
        }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(calibrated, f, indent=4)

    print("\n✅ Calibration complete")
    print(f"📁 Saved to: {output_path}\n")

    print("📊 Biological Ranges:")
    for k, v in calibrated.items():
        print(f"{k:20s} [{v['robust_min']:.3f}, {v['robust_max']:.3f}]")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--real_dir",
        type=str,
        required=True,
        help="Directory containing REAL videos only"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="model/calibrated_thresholds.json",
        help="Path to save calibrated thresholds"
    )
    args = parser.parse_args()

    calibrate(args.real_dir, args.output)
