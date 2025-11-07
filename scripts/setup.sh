#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# ============ STEP 1: Créer dossier data ============
log_info "STEP 1: Creating data directory"

if [ -d ./data ]; then
    log_info "data directory already exists"
else
    mkdir -p ./data
    log_success "Created data directory"
fi

# ============ STEP 2: Builder image Docker ============
log_info "STEP 2: Building Docker image"

if docker build -t streamlit_app:latest .; then
    log_success "Docker image built successfully"
else
    log_error "Failed to build Docker image"
    exit 1
fi

# ============ STEP 3: Vérifier image ============
log_info "STEP 3: Verifying Docker image"

if docker images | grep -q "streamlit_app"; then
    log_success "Docker image verified"
else
    log_error "Docker image not found"
    exit 1
fi

# ============ DONE ============
log_success "✅ SETUP COMPLETE!"
log_info "You can now run: docker-compose up"