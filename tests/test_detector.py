import cv2
import numpy as np
import pytest
from lib.detector_engine import ColorDetectorEngine

def test_extract_template_from_click():
    # Create a dummy image (100x100) with a colored rectangle in the center
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Fill with neutral background
    img[:] = (200, 200, 200) 
    
    # Draw a distinct red rectangle in the center
    # BGR format: red is (0, 0, 255)
    cv2.rectangle(img, (40, 40), (60, 60), (0, 0, 255), -1)
    
    # Click in the middle of the red rectangle
    template = ColorDetectorEngine.extract_template_from_click(img, 50, 50, patch_size=40)
    
    assert template is not None
    assert "lower_bound" in template
    assert "upper_bound" in template
    assert template["area"] > 0
    assert template["width"] > 0
    assert template["height"] > 0

def test_detect_objects():
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img[:] = (200, 200, 200) 
    
    # Draw two red rectangles
    cv2.rectangle(img, (20, 20), (40, 40), (0, 0, 255), -1)
    cv2.rectangle(img, (120, 120), (140, 140), (0, 0, 255), -1)
    
    template = ColorDetectorEngine.extract_template_from_click(img, 30, 30, patch_size=30)
    
    detections, mask = ColorDetectorEngine.detect_objects(
        img, 
        template,
        tolerance=0.5,
        proximity=20.0,
        min_area_scale=0.5,
        max_area_scale=2.0
    )
    
    # Should detect exactly 2 objects
    assert len(detections) == 2
    
    # Verify centroids
    centroids = [d["centroid"] for d in detections]
    
    # One near (30,30) and one near (130,130)
    c1 = next((c for c in centroids if abs(c[0] - 30) < 5), None)
    c2 = next((c for c in centroids if abs(c[0] - 130) < 5), None)
    
    assert c1 is not None
    assert c2 is not None
