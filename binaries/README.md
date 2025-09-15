# FRER Binary Files Directory

This directory contains pre-generated FRER (Frame Replication and Elimination for Reliability) binary configurations for the NXP Gold Box (S32G-VNP-GLDBOX) with SJA1110 TSN switch.

## 📁 Directory Structure

```
binaries/
├── sja1110_uc_*.bin          # UC (Microcontroller) firmware files
├── sja1110_switch_*.bin      # Switch configuration files
├── config_*.json             # JSON configuration descriptions
├── upload.sh                 # Upload helper script
└── README.md                 # This file
```

## 🚀 Quick Usage

```bash
# Upload a scenario (example: test_scenario)
./upload.sh test_scenario

# List available scenarios
ls config_*.json | sed 's/config_//;s/.json//'
```

## 📋 Available Configurations

| Scenario | Description | Streams | Key Feature |
|----------|-------------|---------|-------------|
| `basic_rj45` | Basic RJ45 replication | 2 | Simple P1→P2A,P2B |
| `dual_path` | Dual path redundancy | 2 | Basic 2-way split |
| `triple_redundancy` | Triple redundancy | 3 | 3-way replication |
| `test_scenario` | Comprehensive test | 4 | All features test |
| `rj45_to_automotive` | RJ45 to T1 bridge | 3 | Ethernet to T1 |
| `mixed_automotive` | ECU network | 3 | Automotive focus |
| `redundant_gateway` | HA gateway | 3 | Backup paths |
| `ring_topology` | Ring redundancy | 3 | Ring network |
| `load_balancing` | Load distribution | 2 | Traffic spreading |
| `maximum_replication` | Max replication | 2 | 1→10 ports test |

## 🔍 File Naming Convention

- **UC Files:** `sja1110_uc_<scenario>.bin`
  - Size: 320,280 bytes
  - Contains microcontroller firmware
  - `sja1110_uc_master.bin` works with all switch configs

- **Switch Files:** `sja1110_switch_<scenario>.bin`
  - Size: 655,360+ bytes
  - Contains FRER tables and configuration
  - Scenario-specific replication rules

- **Config Files:** `config_<scenario>.json`
  - Human-readable configuration
  - Stream definitions and port mappings

## 📊 Binary Format

All binaries follow the SJA1110 format:
```
0x000000: IMAGE_VALID_MARKER (0x6AA66AA66AA66AA6)
0x000008: DEVICE_ID (0xb700030e)
0x034000: General Parameters (FRMREPEN=1)
0x080000: CB Sequence Generation Table
0x090000: CB Individual Recovery Table
0x0A0000: DPI Table
End-4:    CRC32 Checksum
```

## 🎯 Scenario Selection

Choose based on your needs:
- **Testing:** Use `test_scenario`
- **Production:** Use `redundant_gateway` or `triple_redundancy`
- **Development:** Start with `basic_rj45`
- **Automotive:** Use `rj45_to_automotive` or `mixed_automotive`
- **Stress Test:** Use `maximum_replication`

## 📝 Example: test_scenario

The most comprehensive configuration with 4 streams:

```json
Stream 1: PFE → P2A, P2B (CPU to external)
Stream 2: P2A → P6, P7 (RJ45 to T1)
Stream 3: P6 → P7, P8 (T1 ring)
Stream 4: P1 → P2A, P2B, P6 (Critical triple)
```

## ⚡ Upload Process

1. **Select scenario:**
   ```bash
   SCENARIO="test_scenario"
   ```

2. **Upload to Gold Box:**
   ```bash
   ./upload.sh $SCENARIO
   ```

3. **Verify:**
   ```bash
   # Check ports
   for i in {0..10}; do
     echo "Port $i: $(cat /sys/class/net/sw0p$i/carrier 2>/dev/null)"
   done
   ```

## 🛠️ Manual Upload

If the script doesn't work, use:
```bash
sudo ../goldbox_dual_upload.sh \
  sja1110_uc_<scenario>.bin \
  sja1110_switch_<scenario>.bin
```

## 📚 More Information

See [BINARY_CATALOG.md](../BINARY_CATALOG.md) for detailed descriptions of each scenario.

## ⚠️ Requirements

- NXP S32G-VNP-GLDBOX hardware
- Root/sudo access
- SJA1110 driver loaded
- Network interfaces configured

---

*Part of the [NXP SJA1110 Control Tool](https://github.com/hwkim3330/nxp-sja1110-control-tool)*