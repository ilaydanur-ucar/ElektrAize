from PIL import Image
from collections import Counter

def get_dominant_color(image_path):
    try:
        img = Image.open(image_path)
        img = img.resize((50, 50))
        pixels = list(img.getdata())
        pixels = [p for p in pixels if len(p) < 4 or p[3] > 0]
        if not pixels: return "No opaque pixels found"
        
        # Filter for yellow-ish colors (R+G high, B low) to avoid picking up the background
        # Simple heuristic: R > 150, G > 150, B < 150
        yellow_pixels = [p for p in pixels if p[0] > 100 and p[1] > 100 and p[2] < 200]
        
        if yellow_pixels:
            counts = Counter(yellow_pixels)
        else:
            counts = Counter(pixels) # Fallback
            
        most_common = counts.most_common(1)[0][0]
        r, g, b = most_common[:3]
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception as e:
        return str(e)

image_path = r"C:/Users/Göksu/.gemini/antigravity/brain/55dd4bbe-b837-4be0-a15f-33020b24a9da/uploaded_image_1766345831854.png"
print(f"Dominant Color: {get_dominant_color(image_path)}")
