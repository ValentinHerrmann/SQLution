"""
pytest configuration for Django tests.
"""
import django
import os
import sys
from pathlib import Path

# Add the tutorial directory to the Python path
# This allows Django to find the tutorial.settings module
tutorial_dir = Path(__file__).resolve().parent.parent.parent.parent / 'tutorial'
sys.path.insert(0, str(tutorial_dir))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')

# Setup Django
django.setup()
