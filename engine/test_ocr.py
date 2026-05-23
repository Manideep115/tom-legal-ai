import pytesseract
from PIL import Image
import os

# --- FALLBACK PATH ---
# If you get a "tesseract is not installed" error, uncomment the line below 
# and make sure it points to your actual installation path:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def test_vision():
    # Update this path if you saved your image somewhere else
    image_path = r"C:\Users\alurm\OneDrive\Desktop\legal_rag_v2\engine\test.png "
    
    if not os.path.exists(image_path):
        print("❌ Error: Could not find 'test.png'. Please check the path.")
        return
        
    print("👀 Tom is looking at the image...")
    
    try:
        # The actual OCR extraction
        extracted_text = pytesseract.image_to_string(Image.open(image_path))
        
        print("\n✅ OCR Success! Here is what Tom read:\n")
        print("-" * 40)
        print(extracted_text.strip())
        print("-" * 40)
        
    except Exception as e:
        print(f"\n❌ OCR Failed. The engines might not be linked correctly.")
        print(f"Error Details: {e}")

if __name__ == "__main__":
    test_vision()