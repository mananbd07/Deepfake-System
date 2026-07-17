import librosa
import numpy as np
import logging

TARGET_SR = 16000
N_MFCC = 20
MIN_DURATION = 1.0  # seconds

logging.basicConfig(level=logging.ERROR)


def extract_features(file_path):
    try:
        # Load audio (librosa already uses audioread/ffmpeg internally)
        y, sr = librosa.load(file_path, sr=TARGET_SR, mono=True)

        if y is None or len(y) == 0:
            raise RuntimeError("No audio data")

        duration = len(y) / sr
        if duration < MIN_DURATION:
            raise RuntimeError("Audio too short")

        y = np.nan_to_num(y)

        # MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)

        features = np.concatenate([
            np.mean(mfcc, axis=1),
            np.mean(delta, axis=1),
            np.mean(delta2, axis=1),
            np.std(mfcc, axis=1)
        ])

        return features.tolist()

    except Exception:
        logging.error("Invalid or unreadable audio file")
        return None
