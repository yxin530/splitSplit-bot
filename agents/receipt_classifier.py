import cv2
import numpy as np

def is_highlighted(image_path: str) -> bool:
    """
    Very naive check to see if an image contains significant highlight colors.
    Returns True if highlighted, False if it appears plain/monochrome.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False

    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define a saturation threshold. Plain text has very low saturation (close to 0)
    # Highlights are typically colorful (high saturation)
    saturation_channel = hsv[:, :, 1]
    
    # Count pixels with saturation > 40
    colorful_pixels = np.sum(saturation_channel > 40)
    
    # If more than 1% of the receipt is highly saturated, assume highlighted
    total_pixels = saturation_channel.size
    ratio = colorful_pixels / total_pixels
    
    return ratio > 0.01
