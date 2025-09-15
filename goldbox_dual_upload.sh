#!/bin/bash
#
# Gold Box SJA1110 Dual Firmware Upload Script
# Uploads both sja1110_uc.bin and sja1110_switch.bin
#

UC_FILE="${1:-sja1110_uc.bin}"
SWITCH_FILE="${2:-sja1110_switch.bin}"
FIRMWARE_DIR="/lib/firmware"
SPI_DEV="/sys/bus/spi/devices/spi0.0"
SWITCH_CFG="${SPI_DEV}/switch-configuration"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Gold Box SJA1110 Dual Firmware Upload Tool${NC}"
echo -e "${GREEN}================================================${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (sudo)${NC}"
    exit 1
fi

# Check files exist
if [ ! -f "$UC_FILE" ]; then
    echo -e "${RED}Error: UC firmware file $UC_FILE not found${NC}"
    exit 1
fi

if [ ! -f "$SWITCH_FILE" ]; then
    echo -e "${RED}Error: Switch config file $SWITCH_FILE not found${NC}"
    exit 1
fi

echo -e "${BLUE}Files to upload:${NC}"
echo -e "  UC Firmware: $UC_FILE ($(ls -lh $UC_FILE | awk '{print $5}'))"
echo -e "  Switch Config: $SWITCH_FILE ($(ls -lh $SWITCH_FILE | awk '{print $5}'))"

# Stop SJA1110 driver if running
echo -e "\n${YELLOW}Stopping SJA1110 driver...${NC}"
if systemctl is-active --quiet sja1110; then
    systemctl stop sja1110
    echo "✓ Driver stopped"
else
    echo "ℹ Driver not running"
fi

# Copy files to firmware directory
echo -e "\n${YELLOW}Copying firmware files...${NC}"
cp "$UC_FILE" "$FIRMWARE_DIR/"
if [ $? -eq 0 ]; then
    echo "✓ Copied $UC_FILE to $FIRMWARE_DIR/"
else
    echo -e "${RED}✗ Failed to copy UC firmware${NC}"
    exit 1
fi

cp "$SWITCH_FILE" "$FIRMWARE_DIR/"
if [ $? -eq 0 ]; then
    echo "✓ Copied $SWITCH_FILE to $FIRMWARE_DIR/"
else
    echo -e "${RED}✗ Failed to copy switch config${NC}"
    exit 1
fi

# Set proper permissions
chmod 644 "$FIRMWARE_DIR/$UC_FILE" "$FIRMWARE_DIR/$SWITCH_FILE"
echo "✓ Set file permissions"

# Start SJA1110 driver
echo -e "\n${YELLOW}Starting SJA1110 driver...${NC}"
systemctl start sja1110
sleep 3

if systemctl is-active --quiet sja1110; then
    echo "✓ Driver started successfully"
else
    echo -e "${YELLOW}⚠ Driver status unclear, checking manually...${NC}"
fi

# Wait for device initialization
echo -e "\n${YELLOW}Waiting for device initialization...${NC}"
sleep 5

# Verify device
echo -e "\n${GREEN}Device Verification:${NC}"

# Check device ID
if [ -f "${SPI_DEV}/device_id" ]; then
    DEVICE_ID=$(cat "${SPI_DEV}/device_id" 2>/dev/null)
    if [ -n "$DEVICE_ID" ]; then
        echo "✓ Device ID: $DEVICE_ID"
    else
        echo "⚠ Device ID not readable"
    fi
else
    echo "⚠ Device ID file not found"
fi

# Check firmware status
if [ -f "${SPI_DEV}/firmware_status" ]; then
    FW_STATUS=$(cat "${SPI_DEV}/firmware_status" 2>/dev/null)
    echo "Firmware Status: $FW_STATUS"
elif [ -f "${SPI_DEV}/status" ]; then
    STATUS=$(cat "${SPI_DEV}/status" 2>/dev/null)
    echo "Device Status: $STATUS"
fi

# Check ports
echo -e "\n${GREEN}Port Status:${NC}"
PORT_COUNT=0
for port in /sys/class/net/sw*p*; do
    if [ -d "$port" ]; then
        PORT_NAME=$(basename $port)
        LINK_STATUS=$(cat "$port/carrier" 2>/dev/null || echo "unknown")
        OPERSTATE=$(cat "$port/operstate" 2>/dev/null || echo "unknown")
        echo "  $PORT_NAME: link=$LINK_STATUS, state=$OPERSTATE"
        PORT_COUNT=$((PORT_COUNT + 1))
    fi
done

if [ $PORT_COUNT -eq 0 ]; then
    echo "⚠ No switch ports found - checking alternative locations..."
    for port in /sys/class/net/eth*; do
        if [ -d "$port" ]; then
            PORT_NAME=$(basename $port)
            echo "  Found: $PORT_NAME"
        fi
    done
fi

# Check FRER configuration if available
echo -e "\n${GREEN}FRER Configuration:${NC}"
if [ -f "${SWITCH_CFG}/frer_status" ]; then
    cat "${SWITCH_CFG}/frer_status"
elif [ -f "${SPI_DEV}/frer_config" ]; then
    echo "FRER config found at: ${SPI_DEV}/frer_config"
    head -5 "${SPI_DEV}/frer_config" 2>/dev/null || echo "Unable to read config"
else
    echo "ℹ FRER status not available via sysfs"
fi

# Show configuration summary
echo -e "\n${GREEN}Configuration Summary:${NC}"
if [ -f "sja1110_firmware_config.json" ]; then
    echo "Configured FRER streams:"
    python3 -c "
import json
try:
    with open('sja1110_firmware_config.json') as f:
        config = json.load(f)
    for stream in config['frer_configuration']['stream_details']:
        print(f\"  • {stream['name']}: Port {stream['src_port']} → {stream['dst_ports']}\")
except:
    print('  Configuration details not available')
"
fi

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}Upload Complete!${NC}"
echo -e "${GREEN}================================================${NC}"

# Show test commands
echo -e "\n${YELLOW}Test Commands:${NC}"
echo "# Monitor FRER replication:"
echo "tcpdump -i sw0p2 -v"
echo "tcpdump -i sw0p3 -v"
echo ""
echo "# Send test traffic from PFE:"
echo "ping -I pfe0 192.168.1.100"
echo ""
echo "# Check replication statistics:"
echo "cat /proc/net/sja1110/stats 2>/dev/null || echo 'Stats not available'"

echo -e "\n${BLUE}Note: Gold Box performs FRER replication only.${NC}"
echo -e "${BLUE}Frame elimination should be configured on receiving devices.${NC}"