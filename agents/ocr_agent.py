import os
import json
from google import genai
from google.genai import types
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def extract_receipt_data(image_path: str) -> dict:
    """
    Extracts structured data from a receipt image using Gemini API.
    Returns a dictionary with items, subtotal, tax, service_charge, total, currency.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set.")
        return None

    try:
        client = genai.Client(api_key=api_key)
        
        # Load image
        img = Image.open(image_path)
        
        prompt = """
        You are a highly capable receipt parsing AI. Analyze this receipt image and extract the following information into a structured JSON format. 
        Even if the receipt is slightly blurry or hard to read, please make your best guess for the items and prices. Do not return an empty list of items unless the image is completely illegible or definitely not a receipt.
        
        Format:
        {
            "items": [
                {
                    "name": "Item name",
                    "quantity": 1,
                    "unit_price": 10.50,
                    "line_total": 10.50,
                    "highlight_color": "pink" // If the item has a marker highlight over it, specify the color (e.g., pink, blue, yellow). If none, return null.
                }
            ],
            "subtotal": 100.00,
            "tax": 6.00,
            "service_charge": 10.00,
            "total": 116.00,
            "currency": "MYR"
        }
        Make sure to return ONLY the raw JSON object, without any markdown formatting like ```json ... ```.
        """
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[prompt, img]
        )
        
        text_response = response.text.strip()
        # Clean up if the model wrapped it in markdown anyway
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]
            
        data = json.loads(text_response.strip())
        return data
        
    except Exception as e:
        logger.error(f"Failed to extract receipt data using Gemini: {e}")
        return None
