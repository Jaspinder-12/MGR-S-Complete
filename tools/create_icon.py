import os
import sys
from PIL import Image, ImageDraw, ImageFont

def create_mgrs_icon(output_dir, size=1024):
    """
    Creates a professional, high-resolution MGR-S icon programmatically.
    """
    # Colors (Slate/Blue/Indigo theme)
    COLOR_BG = "#0F172A"      # Deep Slate (Matches mgrs_gui)
    COLOR_ACCENT = "#3B82F6"  # Electric Blue
    COLOR_SECONDARY = "#6366F1" # Indigo
    COLOR_TEXT = "#F8FAFC"    # Ghost White
    
    # Create master image
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 1. Background Shape (Rounded Square)
    margin = size // 16
    radius = size // 8
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=COLOR_BG,
        outline=COLOR_ACCENT,
        width=size // 64
    )
    
    # 2. Tech Elements (Circuit Traces)
    # We'll draw some abstract diagonal lines to suggest high-speed data
    trace_width = size // 128
    for i in range(4):
        offset = i * (size // 8)
        draw.line([size // 4 + offset, size // 2, size * 3 // 4, size // 4 - offset + size // 2], 
                  fill=f"{COLOR_SECONDARY}44", width=trace_width)
    
    # 3. Central Logo (Stylized 'S' for System/SFR)
    # We'll use a bold, futuristic font if available, otherwise draw it
    try:
        # Try to find a system font
        font_path = "C:/Windows/Fonts/segoeuib.ttf" # Segoe UI Bold
        if not os.path.exists(font_path):
            font_path = "C:/Windows/Fonts/arialbd.ttf"
            
        font_size = int(size * 0.5)
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = None
        
    if font:
        # Draw central 'S' or 'MGR-S'
        text = "S"
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size-w)//2, (size-h)//2), text, fill=COLOR_ACCENT, font=font)
    else:
        # Fallback manual drawing of an abstract S shape
        sw = size // 4
        sh = size // 2
        cx, cy = size // 2, size // 2
        draw.arc([cx-sw, cy-sh//2, cx+sw, cy], 0, 180, fill=COLOR_ACCENT, width=size//32)
        draw.arc([cx-sw, cy, cx+sw, cy+sh//2], 180, 0, fill=COLOR_SECONDARY, width=size//32)

    # 4. Final Polish: Outer glow simulation
    # (Simple enough for a programmatic icon)
    
    # Save outputs
    os.makedirs(output_dir, exist_ok=True)
    
    # Save PNG
    png_path = os.path.join(output_dir, "mgrs_icon.png")
    img.save(png_path, "PNG")
    print(f"Generated: {png_path}")
    
    # Save ICO (multiple sizes)
    ico_path = os.path.join(output_dir, "mgrs_icon.ico")
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format='ICO', sizes=icon_sizes)
    print(f"Generated: {ico_path}")

def generate_msix_assets(source_img_path, output_dir):
    """Generates the specific PNG sizes required for MSIX packaging."""
    from PIL import Image
    img = Image.open(source_img_path)
    os.makedirs(output_dir, exist_ok=True)
    
    sizes = {
        "StoreLogo.png": (50, 50),
        "Square150x150Logo.png": (150, 150),
        "Square44x44Logo.png": (44, 44),
        "Wide310x150Logo.png": (310, 150),
        "SplashScreen.png": (620, 300)
    }
    
    for filename, size in sizes.items():
        # Using Resampling.LANCZOS for quality
        resized = img.resize(size, Image.Resampling.LANCZOS)
        resized.save(os.path.join(output_dir, filename))
        print(f"Generated MSIX asset: {filename}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "j:/MGR-S/ui/resources"
    create_mgrs_icon(out)
