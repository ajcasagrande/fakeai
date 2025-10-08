#!/bin/bash
# Build script for FakeAI dashboard
# This script builds the React dashboard and prepares it for pip packaging

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"
STATIC_DIR="$PROJECT_ROOT/fakeai/static/spa"
DIST_DIR="$DASHBOARD_DIR/dist"

# Parse command line arguments
SKIP_INSTALL=false
CLEAN_ONLY=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-install)
            SKIP_INSTALL=true
            shift
            ;;
        --clean)
            CLEAN_ONLY=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-install    Skip npm install step"
            echo "  --clean           Clean build artifacts and exit"
            echo "  --verbose, -v     Verbose output"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

print_success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

# Clean function
clean_build() {
    print_header "Cleaning build artifacts..."

    if [ -d "$DIST_DIR" ]; then
        rm -rf "$DIST_DIR"
        echo "  - Removed $DIST_DIR"
    fi

    if [ -d "$STATIC_DIR" ]; then
        rm -rf "$STATIC_DIR"
        echo "  - Removed $STATIC_DIR"
    fi

    print_success "Clean completed"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking prerequisites..."

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        echo ""
        echo "Please install Node.js from https://nodejs.org/"
        echo ""
        echo "Installation options:"
        echo "  macOS:   brew install node"
        echo "  Ubuntu:  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
        echo "  Windows: Download from https://nodejs.org/"
        exit 1
    fi

    NODE_VERSION=$(node --version)
    echo "  - Node.js: $NODE_VERSION"

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        echo "npm should come with Node.js. Please reinstall Node.js."
        exit 1
    fi

    NPM_VERSION=$(npm --version)
    echo "  - npm: $NPM_VERSION"

    # Check dashboard directory
    if [ ! -d "$DASHBOARD_DIR" ]; then
        print_error "Dashboard directory not found: $DASHBOARD_DIR"
        exit 1
    fi

    echo "  - Dashboard directory: $DASHBOARD_DIR"

    print_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    if [ "$SKIP_INSTALL" = true ]; then
        print_header "Skipping npm install (--skip-install flag)"
        return
    fi

    print_header "Installing npm dependencies..."

    cd "$DASHBOARD_DIR"

    if [ "$VERBOSE" = true ]; then
        npm install
    else
        npm install --silent --no-progress
    fi

    print_success "Dependencies installed"
}

# Build dashboard
build_dashboard() {
    print_header "Building dashboard..."

    cd "$DASHBOARD_DIR"

    if [ "$VERBOSE" = true ]; then
        npm run build
    else
        npm run build > /dev/null 2>&1
    fi

    print_success "Dashboard built"
}

# Copy to static directory
copy_to_static() {
    print_header "Copying files to static directory..."

    # Check if dist directory exists
    if [ ! -d "$DIST_DIR" ]; then
        print_error "Build directory not found: $DIST_DIR"
        exit 1
    fi

    # Create static directory
    mkdir -p "$STATIC_DIR"

    # Remove old files
    rm -rf "${STATIC_DIR:?}"/*

    # Copy new files
    cp -r "$DIST_DIR"/* "$STATIC_DIR/"

    print_success "Files copied to $STATIC_DIR"
}

# Verify build
verify_build() {
    print_header "Verifying build..."

    # Check if index.html exists
    if [ ! -f "$STATIC_DIR/index.html" ]; then
        print_error "index.html not found in $STATIC_DIR"
        exit 1
    fi

    echo "  - index.html found"

    # List contents
    echo ""
    echo "Build contents:"
    ls -lh "$STATIC_DIR" | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'

    if [ -d "$STATIC_DIR/assets" ]; then
        ASSET_COUNT=$(find "$STATIC_DIR/assets" -type f | wc -l)
        echo "  - assets/ directory with $ASSET_COUNT files"
    fi

    print_success "Build verification passed"
}

# Calculate sizes
calculate_sizes() {
    print_header "Build size information..."

    if command -v du &> /dev/null; then
        TOTAL_SIZE=$(du -sh "$STATIC_DIR" | awk '{print $1}')
        echo "  - Total size: $TOTAL_SIZE"
    fi

    if [ -f "$STATIC_DIR/index.html" ]; then
        INDEX_SIZE=$(ls -lh "$STATIC_DIR/index.html" | awk '{print $5}')
        echo "  - index.html: $INDEX_SIZE"
    fi

    if [ -d "$STATIC_DIR/assets" ]; then
        ASSETS_SIZE=$(du -sh "$STATIC_DIR/assets" 2>/dev/null | awk '{print $1}' || echo "N/A")
        echo "  - assets/: $ASSETS_SIZE"
    fi
}

# Main execution
main() {
    echo "========================================"
    echo "  FakeAI Dashboard Build Script"
    echo "========================================"

    # Handle clean-only mode
    if [ "$CLEAN_ONLY" = true ]; then
        clean_build
        exit 0
    fi

    # Run build process
    check_prerequisites
    install_dependencies
    build_dashboard
    copy_to_static
    verify_build
    calculate_sizes

    # Print summary
    echo ""
    echo "========================================"
    print_success "Dashboard build completed!"
    echo "========================================"
    echo ""
    echo "Dashboard location: $STATIC_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Install the package: pip install -e ."
    echo "  2. Start the server: fakeai serve"
    echo "  3. Access dashboard: http://localhost:8000/spa"
    echo ""
    echo "To build a distribution package:"
    echo "  python -m build"
    echo ""
}

# Run main function
main
