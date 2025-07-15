#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(r'c:\Users\accou\__GITHUB\DataSpark_new\tutorial')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
django.setup()

from myapp.views import generate_qr_svg

# Test QR code generation with circle shape
content = "Test QR Code"
qr_color = "#ff0000"  # Red color to make it obvious
svg_content = generate_qr_svg(content, None, qr_color, "#ffffff", "circle", False)

if svg_content:
    with open(r"c:\Users\accou\__GITHUB\DataSpark_new\tutorial\test_circle_qr.svg", "w") as f:
        f.write(svg_content)
    print("QR code saved to test_circle_qr.svg")
else:
    print("Failed to generate QR code")
