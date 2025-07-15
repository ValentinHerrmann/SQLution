#!/usr/bin/env python
"""Quick test to verify QR generation still works after cleanup"""
import os
import sys
import django

# Setup Django
sys.path.append(r'c:\Users\accou\__GITHUB\DataSpark_new\tutorial')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
django.setup()

from myapp.views import generate_qr_svg

# Test basic QR generation
content = "https://dataspark.example.com"
svg_content = generate_qr_svg(content)

if svg_content and "<svg" in svg_content:
    print("✓ QR generation works correctly")
    print(f"✓ Generated {len(svg_content)} characters of SVG")
else:
    print("✗ QR generation failed")
    
# Clean up
os.remove(__file__)
