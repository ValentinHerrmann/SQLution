"""
pytest configuration for Django tests.
"""
import django
import os
import sys

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tutorial.settings')

# Setup Django
django.setup()
