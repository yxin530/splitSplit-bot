import os
from PIL import Image
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.DEBUG)

# Create a dummy image for testing
img = Image.new('RGB', (100, 100), color = 'white')
img.save('dummy.jpg')

from agents.ocr_agent import extract_receipt_data

try:
    print("Testing OCR...")
    data = extract_receipt_data('dummy.jpg')
    print("Result:", data)
except Exception as e:
    print("Error:", e)
