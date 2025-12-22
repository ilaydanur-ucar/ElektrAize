from PIL import Image
import collections

def get_dominant_color(image_path):
    try:
        img = Image.open(image_path)
        img = img.resize((150, 150))
        img = img.convert("RGBA")
        pixels = img.getdata()
        
        # Count colors
        color_counts = collections.Counter(pixels)
        
        # Get most common color that is not transparent
        for color, count in color_counts.most_common():
            if color[3] > 0: # Check alpha
                return '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                
        return "No color found"
        
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    image_path = r"C:/Users/Göksu/.gemini/antigravity/brain/55dd4bbe-b837-4be0-a15f-33020b24a9da/uploaded_image_1766370555025.png"
    print(get_dominant_color(image_path))
