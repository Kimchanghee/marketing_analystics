#!/usr/bin/env python3
"""Test if the app can be imported without errors"""
import sys
import traceback

print("=" * 50)
print("Testing application imports...")
print("=" * 50)

try:
    print("Importing app.main...")
    from app import main
    print("✓ app.main imported successfully")
    print(f"✓ FastAPI app created: {main.app}")
    print("=" * 50)
    print("SUCCESS: All imports work!")
    print("=" * 50)
    sys.exit(0)
except Exception as e:
    print("=" * 50)
    print("ERROR: Import failed!")
    print("=" * 50)
    print(f"Error: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("=" * 50)
    sys.exit(1)
