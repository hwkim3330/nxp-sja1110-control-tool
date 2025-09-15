#!/bin/bash
# Upload script for FRER binaries
SCENARIO="${1:-test_scenario}"
echo "Uploading scenario: $SCENARIO"
sudo ../goldbox_dual_upload.sh sja1110_uc_${SCENARIO}.bin sja1110_switch_${SCENARIO}.bin
