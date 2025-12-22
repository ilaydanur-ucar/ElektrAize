from PIL import Image
from collections import Counter

def get_dominant_color(image_path):
    try:
        img = Image.open(image_path)
        img = img.resize((50, 50))  # Resize for speed
        pixels = list(img.getdata())
        
        # Remove transparent pixels if any
        pixels = [p for p in pixels if len(p) < 4 or p[3] > 0]
        
        if not pixels:
            return "No opaque pixels found"

        # Count colors
        counts = Counter(pixels)
        most_common = counts.most_common(1)[0][0]
        
        if len(most_common) >= 3:
            r, g, b = most_common[:3]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            return hex_color
        return "Invalid pixel format"
    except Exception as e:
        return str(e)

image_path = r"C:/Users/Göksu/.gemini/antigravity/brain/55dd4bbe-b837-4be0-a15f-33020b24a9da/uploaded_image_1766345238075.png"
print(f"Dominant Color: {get_dominant_color(image_path)}")
