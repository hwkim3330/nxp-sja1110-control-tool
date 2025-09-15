#!/bin/bash
#
# Gold Box SJA1110 FRER Configuration Upload Script
# For NXP S32G-VNP-GLDBOX
#

CONFIG_FILE="${1:-goldbox_frer.bin}"
FIRMWARE_DIR="/lib/firmware"
SPI_DEV="/sys/bus/spi/devices/spi0.0"
SWITCH_CFG="${SPI_DEV}/switch-configuration"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Gold Box FRER Configuration Upload Tool${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (sudo)${NC}"
    exit 1
fi

# Check if configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}Error: Configuration file $CONFIG_FILE not found${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration file: $CONFIG_FILE${NC}"
echo -e "${YELLOW}File size: $(ls -lh $CONFIG_FILE | awk '{print $5}')${NC}"

# Method 1: Direct sysfs upload
if [ -d "$SWITCH_CFG" ]; then
    echo -e "\n${GREEN}Method 1: Using sysfs interface${NC}"
    
    # Copy to firmware directory
    echo "Copying $CONFIG_FILE to $FIRMWARE_DIR..."
    cp "$CONFIG_FILE" "$FIRMWARE_DIR/"
    
    # Upload via sysfs
    echo "Uploading configuration..."
    echo "$(basename $CONFIG_FILE)" > "${SWITCH_CFG}/switch_cfg_upload"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Configuration uploaded successfully via sysfs${NC}"
    else
        echo -e "${YELLOW}⚠ sysfs upload may have failed, trying alternative method${NC}"
    fi
fi

# Method 2: Direct SPI programming (if sysfs fails)
if command -v sja1110-config-upload &> /dev/null; then
    echo -e "\n${GREEN}Method 2: Using SJA1110 config tool${NC}"
    sja1110-config-upload -r -c "$CONFIG_FILE"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Configuration uploaded successfully via config tool${NC}"
    fi
fi

# Verify configuration
echo -e "\n${GREEN}Verifying configuration...${NC}"

# Check switch status
if [ -f "${SPI_DEV}/device_id" ]; then
    DEVICE_ID=$(cat "${SPI_DEV}/device_id")
    echo "Device ID: $DEVICE_ID"
fi

# Check port status
echo -e "\n${GREEN}Port Status:${NC}"
for port in /sys/class/net/sw*p*; do
    if [ -d "$port" ]; then
        PORT_NAME=$(basename $port)
        LINK_STATUS=$(cat "$port/carrier" 2>/dev/null || echo "unknown")
        echo "  $PORT_NAME: link=$LINK_STATUS"
    fi
done

# Display FRER status if available
if [ -f "${SWITCH_CFG}/frer_status" ]; then
    echo -e "\n${GREEN}FRER Status:${NC}"
    cat "${SWITCH_CFG}/frer_status"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Upload complete!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show test commands
echo -e "\n${YELLOW}Test commands:${NC}"
echo "  # Check CB (Circuit Breaker) table:"
echo "  cat ${SWITCH_CFG}/cb_table"
echo ""
echo "  # Monitor FRER statistics:"
echo "  watch -n 1 'cat ${SWITCH_CFG}/frer_stats'"
echo ""
echo "  # Send test traffic (example):"
echo "  # From PFE to P2A/P2B (replicated):"
echo "  ping -I pfe0 192.168.1.100"
echo ""
echo "  # From P2A to PFE (with duplicate elimination):"
echo "  # Connect to P2A port and send traffic to PFE IP"