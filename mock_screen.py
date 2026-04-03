# mock_screen.py

import numpy as np
from PIL import Image, ImageDraw


def create_fake_screenshot(width=1920, height=1080, label="Mock Screen"):
    """Generate a fake screenshot for testing"""
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    # Draw fake UI elements
    draw.rectangle([50, 50, 400, 80], fill=(0, 120, 212), outline="black")
    draw.text((60, 58), "File  Edit  View  Help", fill="white")
    draw.rectangle([50, 100, 800, 600], fill="white", outline="gray")
    draw.text((400, 300), label, fill="black")

    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_fake_accessibility_tree():
    """Generate a fake ACI tree for testing"""
    return {
        "active_app": "MockApp",
        "elements": [
            {"id": 0, "type": "menu", "name": "File", "bounds": [50, 55, 100, 75]},
            {"id": 1, "type": "menu", "name": "Edit", "bounds": [110, 55, 160, 75]},
            {"id": 2, "type": "button", "name": "Save", "bounds": [200, 200, 280, 230]},
            {"id": 3, "type": "textfield", "name": "Content", "bounds": [50, 100, 800, 600]},
        ]
    }

if __name__ == "__main__":
    print(create_fake_screenshot())
    print(create_fake_accessibility_tree())