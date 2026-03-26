"""
Generate PDFOS app icon programmatically using Pillow.
Creates an iOS-style rounded square icon with a document symbol.
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # iOS rounded square background
    r = 100  # corner radius
    # Blue gradient approximation — solid iOS blue
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=r,
        fill=(0, 122, 255)  # iOS blue #007AFF
    )

    # White document shape
    doc_l, doc_t = 140, 80
    doc_r, doc_b = 372, 432
    fold = 70
    doc_points = [
        (doc_l, doc_t + 20),
        (doc_r - fold, doc_t),
        (doc_r, doc_t + fold),
        (doc_r, doc_b - 20),
        (doc_l, doc_b - 20),
    ]
    draw.polygon(doc_points, fill=(255, 255, 255, 230))

    # Fold triangle
    fold_pts = [(doc_r - fold, doc_t), (doc_r, doc_t + fold), (doc_r - fold, doc_t + fold)]
    draw.polygon(fold_pts, fill=(220, 230, 245, 200))

    # "PDF" text on document
    try:
        font = ImageFont.truetype("arial.ttf", 72)
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), "PDF", font=font)
    tw = bbox[2] - bbox[0]
    tx = doc_l + (doc_r - doc_l - tw) // 2
    draw.text((tx, 200), "PDF", fill=(0, 100, 220), font=font)

    # Three horizontal lines (document lines)
    for y_off in [310, 340, 370]:
        draw.rounded_rectangle(
            [(doc_l + 30, y_off), (doc_r - 40, y_off + 8)],
            radius=4,
            fill=(180, 200, 230, 180)
        )

    # Save
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    icon_path = os.path.join(assets_dir, "icon.png")
    img.save(icon_path, "PNG")

    # Also save .ico for Windows
    ico_path = os.path.join(assets_dir, "icon.ico")
    img_ico = img.resize((256, 256), Image.LANCZOS)
    img_ico.save(ico_path, format="ICO", sizes=[(256, 256)])

    print(f"Icons saved to {assets_dir}")
    return icon_path, ico_path


if __name__ == "__main__":
    create_icon()
