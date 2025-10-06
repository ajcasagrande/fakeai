# API Key System Changelog

## Summary

The API key system has been completely refactored to provide a more flexible, secure, and user-friendly authentication mechanism.

## Breaking Changes

### Old System [DEPRECATED]
```bash
# Authentication was required by default
fakeai-server --no-require-api-key  # To disable

# Comma-separated keys
fakeai-server --api-keys "key1,key2,key3"

# Or environment variable
export FAKEAI_API_KEYS="key1,key2,key3"
```

### New System [CURRENT]
```bash
# Authentication disabled by default
fakeai-server  # No auth needed

# Multiple --api-key flags
fakeai-server --api-key key1 --api-key key2 --api-key key3

# Load from files
fakeai-server --api-key /path/to/keys.txt

# Mix both approaches
fakeai-server --api-key direct-key --api-key /path/to/file.txt
```

## Migration Guide

### Scenario 1: No Authentication Needed
**Before:**
```bash
fakeai-server --no-require-api-key
```

**After:**
```bash
fakeai-server  # That's it!
```

### Scenario 2: Multiple Keys via CLI
**Before:**
```bash
fakeai-server --api-keys "sk-key1,sk-key2,sk-key3"
```

**After:**
```bash
fakeai-server --api-key sk-key1 --api-key sk-key2 --api-key sk-key3
```

### Scenario 3: Keys via Environment
**Before:**
```bash
export FAKEAI_REQUIRE_API_KEY=true
export FAKEAI_API_KEYS="sk-key1,sk-key2"
fakeai-server
```

**After:**
```bash
# Still works! Comma-separated for env vars
export FAKEAI_API_KEYS="sk-key1,sk-key2"
fakeai-server

# Or use files (recommended)
echo "sk-key1" > /tmp/keys.txt
echo "sk-key2" >> /tmp/keys.txt
fakeai-server --api-key /tmp/keys.txt
```

## New Features

### 1. File-Based Key Management

Create a keys file:
```
# /etc/fakeai/keys.txt
# Production keys for FakeAI
sk-prod-service-1
sk-prod-service-2

# Team keys
sk-team-alice
sk-team-bob
```

Load it:
```bash
fakeai-server --api-key /etc/fakeai/keys.txt
```

**Benefits:**
- Version control friendly (with .gitignore)
- Easy to manage many keys
- Supports comments and blank lines
- Secure file permissions (chmod 400)

### 2. Multiple Sources

Mix direct keys and files:
```bash
fakeai-server \
  --api-key sk-admin-override \
  --api-key /etc/fakeai/team-keys.txt \
  --api-key /etc/fakeai/service-keys.txt
```

**Benefits:**
- Flexible deployment options
- Emergency admin access
- Separate key categories

### 3. Auto-Enable Authentication

Authentication is automatically enabled when keys are provided:
```bash
# No keys = No auth
fakeai-server

# Keys provided = Auth enabled
fakeai-server --api-key sk-test
```

**Benefits:**
- No need for separate --require-api-key flag
- Intuitive behavior
- Harder to misconfigure

### 4. Better CLI Help

```bash
$ fakeai-server --help
...
API-KEY --api-key          API key or path to file with keys
  --empty-api-key          (one per line). Can be specified
                           multiple times. If not specified,
                           authentication is disabled.
```

## Implementation Details

### Config Changes
```python
# fakeai/config.py

# Before
api_keys: list[str] = Field(
    default_factory=lambda: ["sk-fakeai-...", "sk-test-..."],
)
require_api_key: bool = Field(default=True)

# After
api_keys: list[str] = Field(
    default_factory=list,  # Empty by default
)
require_api_key: bool = Field(default=False)  # Off by default
```

### CLI Changes
```python
# fakeai/cli.py

# New parse_api_keys() function
def parse_api_keys(api_key_sources: list[str]) -> list[str]:
    """Parse keys from direct strings or files."""
    all_keys = []
    for source in api_key_sources:
        if Path(source).is_file():
            # Parse file (skip comments and blanks)
            ...
        else:
            # Direct key
            all_keys.append(source)
    return all_keys

# Auto-enable auth when keys provided
if parsed_keys:
    config_dict["api_keys"] = parsed_keys
    config_dict["require_api_key"] = True
else:
    config_dict["require_api_key"] = False
```

## Testing

Comprehensive test suite added:
- `test_api_key_system.py` - Full integration tests
- Tests default behavior (no auth)
- Tests direct keys
- Tests file parsing
- Tests mixed sources
- Tests auto-enable authentication

All tests pass successfully.

## Security Considerations

### File Permissions

Recommended setup:
```bash
# Create keys file
sudo touch /etc/fakeai/api-keys.txt

# Set ownership
sudo chown fakeai:fakeai /etc/fakeai/api-keys.txt

# Restrict permissions (owner read-only)
sudo chmod 400 /etc/fakeai/api-keys.txt
```

### Key Rotation

Easy rotation with files:
```bash
# Add new keys
echo "sk-new-key-$(date +%s)" >> /etc/fakeai/api-keys.txt

# Restart server
sudo systemctl restart fakeai

# Remove old keys later
vim /etc/fakeai/api-keys.txt  # Comment out old keys
```

### Version Control

Add to `.gitignore`:
```gitignore
# Never commit real keys
api-keys.txt
*-keys.txt
*.key
```

Provide template:
```bash
# api-keys.txt.example
# Copy to api-keys.txt and add your keys
# sk-your-key-here
```

## Documentation

New comprehensive documentation:
- `API_KEY_GUIDE.md` - Complete guide with examples
- `CLI_USAGE.md` - Updated with new API key examples
- `DEMO_API_KEYS.sh` - Interactive demo script

## Backward Compatibility

### Environment Variables

Still supported:
```bash
# Comma-separated in environment
export FAKEAI_API_KEYS="key1,key2,key3"
fakeai-server
```

### Programmatic Usage

Config still works the same:
```python
from fakeai.config import AppConfig

# Manual configuration
config = AppConfig(
    api_keys=["sk-key1", "sk-key2"],
    require_api_key=True
)
```

## Why This Change?

### Problems with Old System
1. Authentication required by default (confusing for development)
2. Comma-separated strings difficult to manage
3. No file support (keys in scripts/env vars)
4. Manual --require-api-key flag needed
5. Not flexible for different deployment scenarios

### Benefits of New System
1. No auth by default (better DX)
2. Multiple --api-key flags (clean CLI)
3. File support (secure, manageable)
4. Auto-enable auth (intuitive)
5. Flexible mixing (production-ready)

## Rollout Checklist

- [x] Update config defaults
- [x] Implement parse_api_keys() function
- [x] Update CLI with new --api-key parameter
- [x] Add auto-enable authentication logic
- [x] Create comprehensive tests
- [x] Update all documentation
- [x] Create migration guide
- [x] Test with real scenarios
- [x] Create demo scripts

## Future Enhancements

Potential additions (not in scope):
- [ ] JWT token support
- [ ] OAuth2 integration
- [ ] Rate limiting per key
- [ ] Key expiration dates
- [ ] Admin API for key management
- [ ] Audit logging per key

## Questions?

See documentation:
- `API_KEY_GUIDE.md` - Complete guide
- `CLI_USAGE.md` - CLI reference
- `DEMO_API_KEYS.sh` - Working examples

Run tests:
```bash
python test_api_key_system.py
```
