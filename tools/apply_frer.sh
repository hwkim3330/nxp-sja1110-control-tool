#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <UC_BIN> <SWITCH_BIN>" >&2
  echo "Example: $0 sja1110_uc.bin sja1110_switch.bin" >&2
}

if [[ ${EUID} -ne 0 ]]; then
  echo "Please run as root (sudo)." >&2
  exit 1
fi

if [[ $# -ne 2 ]]; then
  usage
  exit 1
fi

UC_FILE="$1"
SW_FILE="$2"

if [[ ! -f "$UC_FILE" || ! -f "$SW_FILE" ]]; then
  echo "Firmware files not found: $UC_FILE / $SW_FILE" >&2
  exit 1
fi

FWDIR="/lib/firmware"
echo "Copying firmware to $FWDIR" >&2
cp -f "$UC_FILE" "$FWDIR/"
cp -f "$SW_FILE" "$FWDIR/"
chmod 644 "$FWDIR/$(basename "$UC_FILE")" "$FWDIR/$(basename "$SW_FILE")"

# Detect sysfs endpoints
find_endpoint() {
  local type="$1" # switch-configuration or uc-configuration
  local path
  while IFS= read -r path; do
    if [[ -d "$path" ]]; then
      echo "$path"
      return 0
    fi
  done < <(ls -d /sys/bus/spi/devices/spi*/"$type" 2>/dev/null || true)
  return 1
}

SW_DIR=$(find_endpoint switch-configuration) || {
  echo "switch-configuration endpoint not found under /sys/bus/spi/devices" >&2
  exit 1
}
UC_DIR=$(find_endpoint uc-configuration) || {
  echo "uc-configuration endpoint not found under /sys/bus/spi/devices" >&2
  exit 1
}

echo "Using switch endpoint: $SW_DIR" >&2
echo "Using uc endpoint:     $UC_DIR" >&2

# Upload order: switch then uC
echo "Uploading switch config: $(basename "$SW_FILE")" >&2
echo "$(basename "$SW_FILE")" > "$SW_DIR/switch_cfg_upload"

echo "Uploading uC firmware: $(basename "$UC_FILE")" >&2
echo "$(basename "$UC_FILE")" > "$UC_DIR/uc_fw_upload"

# Optional reset
if [[ -e "$SW_DIR/switch_reset" ]]; then
  echo "Resetting switch" >&2
  echo 1 > "$SW_DIR/switch_reset"
fi

sleep 1

echo "Port states (sw0p*):" >&2
for p in /sys/class/net/sw0p*; do
  [[ -d "$p" ]] || continue
  echo "  $(basename "$p"): link=$(cat "$p"/carrier 2>/dev/null || echo N/A), state=$(cat "$p"/operstate 2>/dev/null || echo N/A)"
done

if [[ -f "$SW_DIR/frer_status" ]]; then
  echo "FRER status:" >&2
  cat "$SW_DIR/frer_status" || true
else
  echo "FRER status not available in sysfs." >&2
fi

echo "Done."

