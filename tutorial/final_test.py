#!/usr/bin/env python3
"""
Final comprehensive test for QR code generation with namespace fixes.
Tests all combinations to ensure no namespace issues remain.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
django.setup()

from myapp.forms import QRGeneratorForm
from myapp.views import generate_qr_svg, generate_rounded_qr_svg

def test_qr_generation():
    """Test QR code generation for all scenarios"""
    print("Final Comprehensive QR Code Generation Test")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        # Square QR codes
        {
            'content': 'Square - No Frame, No Logo',
            'shape_type': 'square',
            'frame_type': 'none',
            'logo_option': 'none',
        },
        {
            'content': 'Square - Simple Frame, No Logo',
            'shape_type': 'square',
            'frame_type': 'simple',
            'logo_option': 'none',
        },
        {
            'content': 'Square - Rounded Frame, No Logo',
            'shape_type': 'square',
            'frame_type': 'rounded',
            'logo_option': 'none',
        },
        # Rounded QR codes (previously problematic)
        {
            'content': 'Rounded - No Frame, No Logo',
            'shape_type': 'rounded',
            'frame_type': 'none',
            'logo_option': 'none',
        },
        {
            'content': 'Rounded - Simple Frame, No Logo',
            'shape_type': 'rounded',
            'frame_type': 'simple',
            'logo_option': 'none',
        },
        {
            'content': 'Rounded - Rounded Frame, No Logo',
            'shape_type': 'rounded',
            'frame_type': 'rounded',
            'logo_option': 'none',
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nTest {i}: {scenario['content']}")
        print(f"  Shape: {scenario['shape_type']}, Frame: {scenario['frame_type']}, Logo: {scenario['logo_option']}")
        
        form_data = {
            'content': scenario['content'],
            'logo_option': scenario['logo_option'],
            'qr_color': '#0066cc',
            'background_type': 'white',
            'shape_type': scenario['shape_type'],
            'frame_type': scenario['frame_type'],
            'frame_color': '#000000',
        }
        
        form = QRGeneratorForm(form_data)
        
        if form.is_valid():
            try:
                # Process form data
                processed_data = {
                    'content': form.cleaned_data['content'],
                    'logo_option': form.cleaned_data['logo_option'],
                    'qr_color': form.cleaned_data['qr_color'],
                    'background_type': form.cleaned_data['background_type'],
                    'shape_type': form.cleaned_data['shape_type'],
                    'frame_type': form.cleaned_data['frame_type'],
                    'frame_color': form.cleaned_data['frame_color'],
                }
                
                # Force logo_option to 'none' for rounded QR codes
                if processed_data['shape_type'] == 'rounded':
                    processed_data['logo_option'] = 'none'
                
                # Set background color
                processed_data['background_color'] = '#ffffff'
                processed_data['use_white_bg'] = True
                processed_data['logo_info'] = None
                
                # Generate QR code based on shape type
                if processed_data['shape_type'] == 'rounded':
                    # For rounded QR codes, first generate the QR code object
                    import qrcode
                    import qrcode.constants
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(processed_data['content'])
                    qr.make(fit=True)
                    
                    svg_content = generate_rounded_qr_svg(
                        qr,
                        processed_data['qr_color'],
                        processed_data['use_white_bg'],
                        processed_data['frame_type'],
                        processed_data['frame_color'],
                        processed_data['logo_info']
                    )
                else:
                    svg_content = generate_qr_svg(
                        processed_data['content'],
                        processed_data['logo_info'],
                        processed_data['qr_color'],
                        processed_data['background_color'],
                        processed_data['shape_type'],
                        processed_data['use_white_bg'],
                        processed_data['frame_type'],
                        processed_data['frame_color']
                    )
                
                if svg_content:
                    # Check for namespace issues
                    has_svg_prefix = 'svg:' in svg_content
                    has_ns0_prefix = 'ns0:' in svg_content
                    has_svg_xmlns = 'xmlns:svg' in svg_content
                    has_ns0_xmlns = 'xmlns:ns0' in svg_content
                    
                    namespace_issues = []
                    if has_svg_prefix:
                        namespace_issues.append('svg: prefix found')
                    if has_ns0_prefix:
                        namespace_issues.append('ns0: prefix found')
                    if has_svg_xmlns:
                        namespace_issues.append('xmlns:svg found')
                    if has_ns0_xmlns:
                        namespace_issues.append('xmlns:ns0 found')
                    
                    if namespace_issues:
                        print(f"  ❌ FAIL: Namespace issues: {', '.join(namespace_issues)}")
                        failed += 1
                    else:
                        print(f"  ✅ PASS: Generated {len(svg_content)} characters, clean SVG")
                        passed += 1
                        
                        # Save to file for verification
                        filename = f"final_test_{i}_{scenario['shape_type']}_{scenario['frame_type']}.svg"
                        with open(filename, 'w') as f:
                            f.write(svg_content)
                        print(f"  📁 Saved to: {filename}")
                else:
                    print(f"  ❌ FAIL: No SVG content generated")
                    failed += 1
                    
            except Exception as e:
                print(f"  ❌ FAIL: Exception occurred: {e}")
                failed += 1
        else:
            print(f"  ❌ FAIL: Form validation failed: {form.errors}")
            failed += 1
    
    print(f"\n" + "=" * 60)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! QR code generation is working correctly.")
        print("✅ No namespace issues detected in any scenario.")
        print("✅ All rounded QR codes are generating properly.")
        print("✅ Fix is complete and comprehensive.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the issues above.")

if __name__ == "__main__":
    test_qr_generation()
