#!/bin/bash
# Demo script showing different ways to use API keys

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                   FakeAI API Key System Demo                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo

# Demo 1: Default (no authentication)
echo "1. DEFAULT - No authentication"
echo "   Command: fakeai-server"
echo "   Result: Server runs with DISABLED authentication"
echo

# Demo 2: Direct keys
echo "2. DIRECT KEYS - Specify keys on command line"
echo "   Command: fakeai-server --api-key sk-test-1 --api-key sk-test-2"
echo "   Result: Authentication ENABLED with 2 keys"
echo

# Demo 3: File-based keys
echo "3. FILE-BASED KEYS - Load from file"
echo "   First, create a keys file:"
cat > /tmp/demo-keys.txt << 'EOF'
# Demo API Keys
sk-demo-alice-key123
sk-demo-bob-key456
sk-demo-charlie-key789
EOF
echo "   File created: /tmp/demo-keys.txt"
cat /tmp/demo-keys.txt
echo
echo "   Command: fakeai-server --api-key /tmp/demo-keys.txt"
echo "   Result: Authentication ENABLED with 3 keys from file"
echo

# Demo 4: Mixed approach
echo "4. MIXED APPROACH - Combine direct keys and files"
echo "   Command:"
echo "     fakeai-server \\"
echo "       --api-key sk-admin-direct \\"
echo "       --api-key /tmp/demo-keys.txt \\"
echo "       --api-key sk-backup-direct"
echo "   Result: Authentication ENABLED with 5 keys total"
echo "           (1 direct + 3 from file + 1 direct)"
echo

# Test parsing
echo "═══════════════════════════════════════════════════════════════════════"
echo "TESTING: Verify key parsing"
python3 << 'PYEOF'
from fakeai.cli import parse_api_keys

# Test file parsing
keys = parse_api_keys([
    "sk-direct-1",
    "/tmp/demo-keys.txt",
    "sk-direct-2"
])

print(f"✓ Parsed {len(keys)} keys:")
for i, key in enumerate(keys, 1):
    print(f"  {i}. {key}")
PYEOF

echo
echo "═══════════════════════════════════════════════════════════════════════"
echo "PRODUCTION EXAMPLE"
echo
echo "Create production keys file:"
echo "  sudo mkdir -p /etc/fakeai"
echo "  sudo vim /etc/fakeai/api-keys.txt"
echo
echo "Add keys (one per line):"
echo "  # Production API Keys"
echo "  sk-prod-service-1-abc123"
echo "  sk-prod-service-2-def456"
echo
echo "Set permissions:"
echo "  sudo chmod 400 /etc/fakeai/api-keys.txt"
echo "  sudo chown fakeai:fakeai /etc/fakeai/api-keys.txt"
echo
echo "Start server:"
echo "  fakeai-server --host 0.0.0.0 --port 8000 --api-key /etc/fakeai/api-keys.txt"
echo
echo "═══════════════════════════════════════════════════════════════════════"
echo "✅ API Key System Demo Complete!"
echo
