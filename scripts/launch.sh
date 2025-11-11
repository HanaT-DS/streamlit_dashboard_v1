#!/bin/bash

# ============================================
# COLORS
# ============================================
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ============================================
# FUNCTIONS
# ============================================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# ============================================
# STEP 1: VERIFY DOCKER
# ============================================
log_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log_error "Docker not found!"
    exit 1
fi
log_success "Docker found"

# ============================================
# STEP 2: VERIFY docker-compose
# ============================================
log_info "Checking docker-compose installation..."
if ! command -v docker-compose &> /dev/null; then
    log_error "docker-compose not found!"
    exit 1
fi
log_success "docker-compose found"

# ============================================
# STEP 3: VERIFY docker-compose.yml
# ============================================
log_info "Checking docker-compose.yml..."
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml not found!"
    exit 1
fi
log_success "docker-compose.yml found"

# ============================================
# STEP 4: EXTRACT DATA FROM GOOGLE DRIVE
# ============================================
log_info "Extracting data from Google Drive..."
bash scripts/data_getter.sh
if [ $? -ne 0 ]; then
    log_error "Failed to extract data"
    exit 1
fi
log_success "Data extracted"

# ============================================
# STEP 5: START APPLICATION
# ============================================
log_success "✅ All checks passed!"
log_info ""
log_info "🚀 Launching Streamlit Application..."
log_info ""
log_warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_warn "App at: http://localhost:8501"
log_warn "Ctrl+C to stop"
log_warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info ""

docker-compose up

log_info ""
log_info "Application stopped"