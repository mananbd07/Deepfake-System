import cv2
import numpy as np
import os

def perform_ela(image_path, temp_dir="uploads"):
    # Read image
    original = cv2.imread(image_path)
    if original is None:
        return None
        
    # Save with specific quality to induce compression difference
    temp_path = os.path.join(temp_dir, "temp_ela.jpg")
    cv2.imwrite(temp_path, original, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # Read back the saved image
    compressed = cv2.imread(temp_path)
    
    # Calculate absolute difference
    diff = cv2.absdiff(original, compressed)
    
    # Enhance difference for visual analysis or heuristic
    max_diff = np.max(diff)
    if max_diff == 0:
        max_diff = 1 # Avoid division by zero
        
    scale = 255.0 / max_diff
    enhanced_diff = np.clip(diff * scale, 0, 255).astype(np.uint8)
    
    # Cleanup temp file
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return enhanced_diff

def analyze_image(image_path, temp_dir="uploads"):
    ela = perform_ela(image_path, temp_dir)
    if ela is None:
        return {"verdict": "ERROR", "confidence": 0, "message": "Could not read image"}
        
    # Convert to grayscale to analyze intensity
    gray_ela = cv2.cvtColor(ela, cv2.COLOR_BGR2GRAY)
    
    # Calculate metrics
    mean_diff = np.mean(gray_ela)
    std_diff = np.std(gray_ela)
    max_diff = np.max(gray_ela)
    
    # Simple heuristic: deepfakes/manipulations often have high localized variance
    # Authentic images usually have relatively uniform compression
    anomaly_score = (std_diff / (mean_diff + 1e-5)) * (max_diff / 255.0)
    
    if anomaly_score > 1.2:
        verdict = "DEEPFAKE"
        # Map anomaly score > 1.2 to 50-100% confidence
        confidence = min(100, int(50 + (anomaly_score - 1.2) * 20))
    else:
        verdict = "REAL"
        # Map anomaly score < 1.2 to 50-100% confidence
        confidence = min(100, int(100 - (anomaly_score / 1.2) * 50))
        
    return {
        "verdict": verdict,
        "confidence": confidence,
        "metrics": {
            "mean_ela": float(mean_diff),
            "std_ela": float(std_diff),
            "anomaly_score": float(anomaly_score)
        }
    }
