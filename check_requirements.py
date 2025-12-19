#!/usr/bin/env python3
"""
Check and verify all required dependencies are installed.
"""
import sys
import importlib.util


REQUIRED_PACKAGES = {
    "fastapi": "FastAPI web framework",
    "uvicorn": "ASGI server",
    "sqlmodel": "SQL database ORM",
    "pydantic": "Data validation",
    "pydantic_settings": "Settings management",
    "jinja2": "Template engine",
    "python-multipart": "Form data parsing",
    "passlib": "Password hashing",
    "python-jose": "JWT token handling",
}

OPTIONAL_PACKAGES = {
    "httpx": "HTTP client for API calls",
    "aiofiles": "Async file operations",
    "pillow": "Image processing",
    "google-generativeai": "Gemini AI integration",
}


def check_package(package_name: str) -> bool:
    """Check if a package is installed."""
    spec = importlib.util.find_spec(package_name.replace("-", "_"))
    return spec is not None


def main():
    """Check all required and optional dependencies."""
    print("🔍 Checking Python dependencies...\n")

    missing_required = []
    missing_optional = []

    # Check required packages
    print("📦 Required packages:")
    for package, description in REQUIRED_PACKAGES.items():
        installed = check_package(package)
        status = "✅" if installed else "❌"
        print(f"  {status} {package:25} - {description}")
        if not installed:
            missing_required.append(package)

    print()

    # Check optional packages
    print("📦 Optional packages:")
    for package, description in OPTIONAL_PACKAGES.items():
        installed = check_package(package)
        status = "✅" if installed else "⚠️ "
        print(f"  {status} {package:25} - {description}")
        if not installed:
            missing_optional.append(package)

    print()

    # Summary
    if missing_required:
        print("❌ Missing required packages:")
        for package in missing_required:
            print(f"   - {package}")
        print("\n📥 Install them with:")
        print(f"   pip install {' '.join(missing_required)}")
        print()
        return 1

    if missing_optional:
        print("⚠️  Missing optional packages:")
        for package in missing_optional:
            print(f"   - {package}")
        print("\n📥 Install them with:")
        print(f"   pip install {' '.join(missing_optional)}")
        print()

    print("✅ All required dependencies are installed!")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
