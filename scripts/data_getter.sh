#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# ============================================
# GOOGLE DRIVE FILE IDs
# ============================================

CLAIMS_ID="1tnGjcW7iGt1Bk2DNTNmUt11N8SRodukR"
CUSTOMERS_ID="1KiZHcH8NVEjRkEU23fVo6HXyzyR-BQaS"
ORDER_PRODUCT_ID="19YeYEylQI0My55VS9NPU3SmomLws5k5m"
ORDER_ROUTE_LEG_ID="1v4NPP_N_Mkj_of-d2rh4V0sPI_nxJxcI"
ORDERS_ID="1gDCSeaTcGTrw0SfHaydPRNPC4LGtlauS"
PRODUCTS_ID="1dt_0epycTe8A6GcbS6SMThIQUv5BGlhO"
STATES_RISK_ID="1pubgis7FWMBAv1EUpW00NjknSD3twBR1"
TRANSPORT_MODE_ID="19VuTgH6L7cNDy0Bgpono5T37APSILZuR"

log_info "Getting data from Google Drive"

# ============================================
# Fonction pour télécharger depuis Google Drive
# ============================================
download_from_gdrive() {
    local file_id=$1
    local output_path=$2
    
    log_info "Downloading: $output_path"
    
    curl -L "https://drive.google.com/uc?export=download&id=$file_id" \
         -o "$output_path" 2>/dev/null
    
    if [ -f "$output_path" ]; then
        log_success "Downloaded: $output_path"
    else
        log_error "Failed to download: $output_path"
        exit 1
    fi
}

# ============================================
# Créer dossier data 
# ============================================
log_info "Creating data directory..."

if [ -d ./data ]; then
    log_info "data directory already exists"
else
    mkdir -p ./data
    log_success "Created data directory"
fi

# ============================================
# Télécharger TOUS les fichiers
# ============================================
download_from_gdrive "$CLAIMS_ID" "./data/claims.csv"
download_from_gdrive "$CUSTOMERS_ID" "./data/customers.csv"
download_from_gdrive "$ORDER_PRODUCT_ID" "./data/order_product.csv"
download_from_gdrive "$ORDER_ROUTE_LEG_ID" "./data/order_route_leg.csv"
download_from_gdrive "$ORDERS_ID" "./data/orders.csv"
download_from_gdrive "$PRODUCTS_ID" "./data/products.csv"
download_from_gdrive "$STATES_RISK_ID" "./data/states_risk.csv"
download_from_gdrive "$TRANSPORT_MODE_ID" "./data/transport_mode.csv"

log_success "✅ All data downloaded from Google Drive!"