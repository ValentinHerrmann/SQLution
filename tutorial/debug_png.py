#!/usr/bin/env python
"""
Debug script to find PNG generation issues
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/mnt/c/Users/accou/__GITHUB/DataSpark_new/tutorial')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
django.setup()

from myapp.views import generate_qr_svg, generate_qr_png

def debug_png_generation():
    """Debug PNG generation step by step"""
    print("Debugging PNG generation...")
    
    # Test parameters
    content = "https://sqlution.de"
    logo_info = None
    qr_color = "#000000"
    background_color = "#ffffff"
    shape_type = "square"
    use_white_bg = False
    frame_type = "rounded"
    frame_color = "#000000"
    png_size = 512
    
    print(f"1. Testing SVG generation...")
    try:
        svg_content = generate_qr_svg(content, logo_info, qr_color, background_color, shape_type, use_white_bg, frame_type, frame_color)
        if svg_content:
            print(f"✓ SVG generated successfully (length: {len(svg_content)})")
            print(f"SVG preview: {svg_content[:200]}...")
        else:
            print("✗ SVG generation failed")
            return
    except Exception as e:
        print(f"✗ SVG generation error: {e}")
        return
    
    print(f"\n2. Testing cairosvg import...")
    try:
        import cairosvg
        print("✓ cairosvg imported successfully")
    except ImportError as e:
        print(f"✗ cairosvg import failed: {e}")
        return
    
    print(f"\n3. Testing SVG to PNG conversion...")
    try:
        png_bytes = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=png_size,
            output_height=png_size
        )
        if png_bytes:
            print(f"✓ PNG conversion successful (bytes length: {len(png_bytes)})")
        else:
            print("✗ PNG conversion returned None")
            return
    except Exception as e:
        print(f"✗ PNG conversion error: {e}")
        return
        
    print(f"\n4. Testing PIL Image creation...")
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(png_bytes))
        print(f"✓ PIL Image created successfully with size: {img.size}")
        return img
    except Exception as e:
        print(f"✗ PIL Image creation error: {e}")
        return

if __name__ == "__main__":
    debug_png_generation()
