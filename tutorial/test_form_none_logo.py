#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(r'c:\Users\accou\__GITHUB\DataSpark_new\tutorial')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
django.setup()

from myapp.forms import QRGeneratorForm

# Test form submission with 'none' logo option
form_data = {
    'content': 'Test QR Code Content',
    'logo_option': 'none',  # This is what "Kein Logo" maps to
    'qr_color': '#0066cc',
    'background_type': 'transparent',
    'frame_type': 'none',
    'frame_color': '#000000'
}

print("Testing form with 'none' logo option...")
form = QRGeneratorForm(data=form_data)

if form.is_valid():
    print("✓ Form is valid!")
    print(f"Logo option: {form.cleaned_data['logo_option']}")
    print(f"Content: {form.cleaned_data['content']}")
    
    # Now test the actual QR generation logic from the view
    from myapp.views import generate_qr_svg
    
    content = form.cleaned_data['content']
    logo_option = form.cleaned_data['logo_option']
    qr_color = form.cleaned_data['qr_color']
    background_type = form.cleaned_data['background_type']
    shape_type = 'square'  # Fixed to square since shape option is removed
    frame_type = form.cleaned_data['frame_type']
    frame_color = form.cleaned_data['frame_color']
    
    # Convert background_type to background_color for processing
    background_color = '#ffffff' if background_type == 'white' else '#ffffff'
    use_white_bg = background_type == 'white'
    
    # Process logo based on selection - this is the key logic
    logo_info = None
    if logo_option == 'dataspark' and shape_type != 'rounded':
        print("Would process DataSpark logo (but skipping for test)")
    elif logo_option == 'custom' and shape_type != 'rounded':
        print("Would process custom logo (but none provided)")
    elif logo_option == 'none':
        print("✓ Logo option is 'none' - logo_info will remain None")
    
    print(f"Final logo_info: {logo_info}")
    
    # Generate QR code
    svg_content = generate_qr_svg(content, logo_info, qr_color, background_color, shape_type, use_white_bg, frame_type, frame_color)
    
    if svg_content:
        print("✓ QR code generated successfully!")
        with open("test_form_none_logo.svg", "w") as f:
            f.write(svg_content)
        print("✓ QR code saved to test_form_none_logo.svg")
    else:
        print("✗ Failed to generate QR code")
        
else:
    print("✗ Form is invalid!")
    print(f"Errors: {form.errors}")
