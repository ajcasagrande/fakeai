#!/bin/bash
# Configure dashboard backend URL for development mode

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== FakeAI Dashboard Backend Configuration ===${NC}\n"

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

# Ask user for backend URL
echo -e "${YELLOW}Where is your FakeAI backend server running?${NC}"
echo ""
echo "Common options:"
echo "  1) http://localhost:8000  (default)"
echo "  2) http://localhost:9002  (custom port)"
echo "  3) Custom URL"
echo ""
read -p "Enter option [1-3] or URL: " choice

case $choice in
  1)
    BACKEND_URL="http://localhost:8000"
    ;;
  2)
    BACKEND_URL="http://localhost:9002"
    ;;
  3)
    read -p "Enter backend URL (e.g., http://localhost:9000): " BACKEND_URL
    ;;
  http*)
    BACKEND_URL="$choice"
    ;;
  *)
    echo -e "${YELLOW}Using default: http://localhost:8000${NC}"
    BACKEND_URL="http://localhost:8000"
    ;;
esac

# Update or create .env file
if [ -f "$ENV_FILE" ]; then
  # Update existing VITE_BACKEND_URL
  if grep -q "^VITE_BACKEND_URL=" "$ENV_FILE"; then
    # Update existing line
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      sed -i '' "s|^VITE_BACKEND_URL=.*|VITE_BACKEND_URL=$BACKEND_URL|" "$ENV_FILE"
    else
      # Linux
      sed -i "s|^VITE_BACKEND_URL=.*|VITE_BACKEND_URL=$BACKEND_URL|" "$ENV_FILE"
    fi
    echo -e "${GREEN}✓${NC} Updated $ENV_FILE"
  else
    # Add new line
    echo "VITE_BACKEND_URL=$BACKEND_URL" >> "$ENV_FILE"
    echo -e "${GREEN}✓${NC} Added VITE_BACKEND_URL to $ENV_FILE"
  fi
else
  # Create new .env file
  cat > "$ENV_FILE" <<EOF
# FakeAI Dashboard Environment Variables
# For local development with Vite

# Backend URL (where your FakeAI backend server is running)
VITE_BACKEND_URL=$BACKEND_URL

# Optional: API Key (leave empty if not required for local dev)
VITE_API_KEY=

# Node environment
NODE_ENV=development
EOF
  echo -e "${GREEN}✓${NC} Created $ENV_FILE"
fi

echo ""
echo -e "${GREEN}Configuration complete!${NC}"
echo ""
echo "Backend URL: $BACKEND_URL"
echo ""
echo "Next steps:"
echo "  1. Start your backend server:"
echo -e "     ${BLUE}python -m fakeai.cli server${NC}"
echo ""
echo "  2. Start the dev server:"
echo -e "     ${BLUE}cd $SCRIPT_DIR && npm run dev${NC}"
echo ""
echo "  3. Open browser:"
echo -e "     ${BLUE}http://localhost:5173${NC}"
echo ""
