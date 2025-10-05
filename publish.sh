#!/bin/bash
set -e

echo "=== FakeAI Publishing Script ==="

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Install publishing dependencies
echo "Installing publishing dependencies..."
pip install --upgrade build twine

# Clean old build artifacts
echo "Cleaning old build artifacts..."
rm -rf dist/ build/ *.egg-info/

# Build the package
echo "Building package..."
python -m build

# Check the build
echo "Checking package with twine..."
twine check dist/*

echo ""
echo "=== Build Complete ==="
echo "Contents of dist/:"
ls -lh dist/

echo ""
echo "Next steps:"
echo "1. Test upload to TestPyPI (optional):"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "2. Upload to PyPI:"
echo "   twine upload dist/*"
echo ""
echo "You will be prompted for your PyPI credentials."
echo "Alternatively, set up a PyPI API token in ~/.pypirc"
