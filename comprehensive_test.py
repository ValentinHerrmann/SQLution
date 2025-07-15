#!/usr/bin/env python3
"""
Comprehensive test for QR code generation with namespace fixes.
Tests all combinations of shape, frame, and logo options.
"""

import os
import sys
import django
from django.conf import settings

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')
django.setup()

from tutorial.myapp.forms import QRGeneratorForm
from tutorial.myapp.views import generate_qr_code

def test_qr_generation():
    """Test QR code generation for all scenarios"""
    print("Comprehensive QR Code Generation Test")
    print("=" * 50)
    
    # Test scenarios
    scenarios = [
        # Square QR codes
        {
            'content': 'Square - No Frame, No Logo',
            'shape_type': 'square',
            'frame_type': 'none',
            'logo_option': 'none',
            'expected_working': True
        },
        {
            'content': 'Square - Simple Frame, No Logo',
            'shape_type': 'square',
            'frame_type': 'simple',
            'logo_option': 'none',
            'expected_working': True
        },
        {
            'content': 'Square - Rounded Frame, No Logo',
            'shape_type': 'square',
            'frame_type': 'rounded',
            'logo_option': 'none',
            'expected_working': True
        },
        # Rounded QR codes
        {
            'content': 'Rounded - No Frame, No Logo',
            'shape_type': 'rounded',
            'frame_type': 'none',
            'logo_option': 'none',
            'expected_working': True
        },
        {
            'content': 'Rounded - Simple Frame, No Logo',
            'shape_type': 'rounded',
            'frame_type': 'simple',
            'logo_option': 'none',
            'expected_working': True
        },
        {
            'content': 'Rounded - Rounded Frame, No Logo',
            'shape_type': 'rounded',
            'frame_type': 'rounded',
            'logo_option': 'none',
            'expected_working': True
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nTest {i}: {scenario['content']}")
        print(f"Shape: {scenario['shape_type']}, Frame: {scenario['frame_type']}, Logo: {scenario['logo_option']}")
        
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
                result = generate_qr_code(form)
                svg_content = result.get('svg_content', '')
                
                if svg_content:
                    # Check for namespace issues
                    has_namespace_issues = ('ns0:' in svg_content or 
                                          'svg:' in svg_content or 
                                          'xmlns:ns0' in svg_content or 
                                          'xmlns:svg' in svg_content)
                    
                    if has_namespace_issues:
                        print(f"  ❌ FAIL: Contains namespace issues")
                        failed += 1
                    else:
                        print(f"  ✅ PASS: Generated {len(svg_content)} characters, no namespace issues")
                        passed += 1
                        
                        # Save to file for verification
                        filename = f"test_{i}_{scenario['shape_type']}_{scenario['frame_type']}.svg"
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
    
    print(f"\n" + "=" * 50)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print(f"Success rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 All tests passed! QR code generation is working correctly.")
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the issues above.")

if __name__ == "__main__":
    test_qr_generation()
