# Publishing to PyPI

This guide walks you through publishing the FakeAI package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts at:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing, optional)

2. **API Tokens**: Generate API tokens for secure authentication:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

## Quick Publishing

### Option 1: Using the Publish Script (Recommended)

```bash
# Build the package
./publish.sh

# Upload to PyPI
twine upload dist/*
```

### Option 2: Manual Steps

```bash
# Activate virtual environment
source .venv/bin/activate

# Install publishing tools
pip install --upgrade build twine

# Clean old artifacts
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build

# Check the build
twine check dist/*

# Upload to PyPI
twine upload dist/*
```

## Setting Up API Tokens

### Method 1: Using .pypirc (Recommended)

Create `~/.pypirc` in your home directory:

```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_API_TOKEN_HERE
```

**Security Note**: Keep this file secure with `chmod 600 ~/.pypirc`

A template is provided at `.pypirc.example` in this repository.

### Method 2: Environment Variables

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_API_TOKEN_HERE
```

## Testing on TestPyPI (Optional but Recommended)

Before publishing to production PyPI, test on TestPyPI:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ fakeai

# Test the package
fakeai-server --version
```

## Version Management

### Updating Version

Edit `pyproject.toml`:

```toml
[project]
version = "0.0.6"  # Increment version
```

### Version Guidelines

Follow [Semantic Versioning](https://semver.org/):

- `0.0.x` - Bug fixes and minor changes
- `0.x.0` - New features (backward compatible)
- `x.0.0` - Breaking changes

## Pre-Publishing Checklist

Before publishing, verify:

- [ ] Version number updated in `pyproject.toml`
- [ ] `README.md` updated with new features
- [ ] All tests passing: `pytest`
- [ ] Code formatted: `black fakeai/` and `isort fakeai/`
- [ ] Type checks passing: `mypy fakeai/`
- [ ] Git changes committed
- [ ] Git tag created: `git tag v0.0.5 && git push origin v0.0.5`

## Publishing Workflow

### Complete Workflow

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml

# 2. Update README if needed
vim README.md

# 3. Run tests
pytest

# 4. Format code
black fakeai/
isort fakeai/

# 5. Commit changes
git add -A
git commit -m "Release v0.0.5"

# 6. Create git tag
git tag v0.0.5
git push origin main --tags

# 7. Build package
./publish.sh

# 8. (Optional) Test on TestPyPI
twine upload --repository testpypi dist/*

# 9. Upload to PyPI
twine upload dist/*

# 10. Verify installation
pip install --upgrade fakeai
fakeai-server --version
```

## Troubleshooting

### "File already exists"

This error means the version already exists on PyPI. You must increment the version number in `pyproject.toml`.

### "Invalid username/password"

- Ensure you're using `__token__` as username (with double underscores)
- Verify your API token is correct and not expired
- Check your `~/.pypirc` file permissions: `chmod 600 ~/.pypirc`

### "Package validation failed"

Run `twine check dist/*` to see validation errors. Common issues:

- Missing or invalid `README.md`
- Invalid metadata in `pyproject.toml`
- Missing required fields (name, version, description)

### Build fails

```bash
# Clean everything and rebuild
rm -rf dist/ build/ *.egg-info/ __pycache__/
python -m build
```

## Advanced: Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install --upgrade build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI API token as `PYPI_API_TOKEN` in GitHub repository secrets.

## Package Structure

The build process includes:

```
dist/
 fakeai-0.0.5-py3-none-any.whl  # Wheel distribution
 fakeai-0.0.5.tar.gz            # Source distribution
```

Both files are uploaded to PyPI.

## Post-Publishing

After publishing:

1. **Verify on PyPI**: https://pypi.org/project/fakeai/
2. **Test installation**: `pip install fakeai`
3. **Update documentation** with any PyPI-specific information
4. **Announce release** in relevant channels

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Setuptools Documentation](https://setuptools.pypa.io/)
- [Twine Documentation](https://twine.readthedocs.io/)

## Support

For publishing issues:
- Check [PyPI Status](https://status.python.org/)
- Visit [Python Packaging Discourse](https://discuss.python.org/c/packaging/)
- Open an issue on GitHub
