# face_tracker.py - Face Detection for Smart Cropping
"""
Modul untuk mendeteksi wajah dalam video dan menentukan posisi crop optimal.
Menggunakan MediaPipe Face Detection.
"""
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
import sys

# Suppress MediaPipe logging
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class FaceTracker:
    def __init__(self, model_selection=1, min_detection_confidence=0.5):
        """
        Initialize FaceTracker.
        model_selection: 0 for close range (2m), 1 for far range (5m)
        """
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_detection_confidence
        )

    def get_average_face_position(self, video_path: str, sample_interval: int = 10) -> float:
        """
        Scan video dan hitung rata-rata posisi X wajah (normalized 0.0 - 1.0).
        Return None jika tidak ada wajah terdeteksi.
        
        Args:
            video_path: Path to video file
            sample_interval: Process every Nth frame (optimization)
            
        Returns:
            float: Average X position of face center (0.0 = left, 1.0 = right)
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            print(f"[WARN] Error opening video for face detection: {video_path}")
            return None

        centers = []
        frame_count = 0
        
        while cap.isOpened():
            # Grab next frame (much faster than decoding via read())
            if not cap.grab():
                break
            
            # Skip frames for performance without decoding
            if frame_count % sample_interval != 0:
                frame_count += 1
                continue

            # Retrieve (decode) frame only when needed
            ret, frame = cap.retrieve()
            if not ret:
                break

            # Convert BGR to RGB
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.face_detection.process(rgb_frame)
                
                if results.detections:
                    # Ambil wajah dengan confidence maintain terbesar (biasanya yang utama)
                    # MediaPipe sorts by score descending by default
                    detection = results.detections[0]
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Calculate center X
                    center_x = bbox.xmin + (bbox.width / 2)
                    centers.append(center_x)
            except Exception as e:
                # Ignore errors in single frames
                pass
                
            frame_count += 1

        cap.release()
        
        if not centers:
            return None
            
        # Remove outliers? Nah, simple average is usually fine for talking heads
        avg_x = sum(centers) / len(centers)
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, avg_x))

    def close(self):
        self.face_detection.close()

def smart_crop_options(input_path: str) -> dict:
    """
    Analisis video dan return parameter crop untuk FFmpeg.
    """
    tracker = FaceTracker()
    try:
        avg_x = tracker.get_average_face_position(input_path)
    except Exception as e:
        print(f"[WARN] Face detection failed: {e}")
        avg_x = None
    finally:
        tracker.close()
        
    if avg_x is None:
        print("   [FACE] No face detected, using center crop.")
        return None
        
    print(f"   [FACE] Face detected at relative X: {avg_x:.2f}")
    return {"center_x": avg_x}
