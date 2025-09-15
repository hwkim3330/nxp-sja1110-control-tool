# FRER Binary Catalog for Gold Box

## 📚 Binary Files Overview

This catalog documents all FRER (Frame Replication and Elimination for Reliability) binary configurations available for the NXP S32G-VNP-GLDBOX (Gold Box) platform with SJA1110 TSN switch.

## 🎯 Quick Start

```bash
# Upload a specific scenario
cd binaries
./upload.sh <scenario_name>

# Example: Upload test scenario
./upload.sh test_scenario
```

## 📦 Binary File Structure

Each scenario consists of two binary files:
- **UC Binary** (`sja1110_uc_*.bin`): Microcontroller firmware (320,280 bytes)
- **Switch Binary** (`sja1110_switch_*.bin`): Switch configuration with FRER tables (655,360+ bytes)

### Binary Header Format
```
Offset      | Content                    | Size
------------|----------------------------|----------
0x000000    | IMAGE_VALID_MARKER         | 8 bytes
0x000008    | DEVICE_ID (0xb700030e)     | 4 bytes
0x00000C    | Configuration Flags        | 4 bytes
0x034000    | General Parameters         |
            | - FRMREPEN (0x01)          | 4 bytes
0x080000    | CB Sequence Gen Table      | Variable
0x090000    | CB Individual Recovery     | Variable
0x0A0000    | DPI Table                  | Variable
End-4       | CRC32 Checksum             | 4 bytes
```

## 🗂️ Available Scenarios

### 1. **basic_rj45** - Basic RJ45 Frame Replication
**Use Case:** Simple frame replication between RJ45 ports

| Stream | Source | Destinations | VLAN | Description |
|--------|--------|--------------|------|-------------|
| 1 | P1 (100M) | P2A, P2B (1G) | 100 | Uplink replication |
| 2 | P2A (1G) | P1, P3 | 200 | Downlink distribution |

**Files:**
- `sja1110_uc_basic_rj45.bin`
- `sja1110_switch_basic_rj45.bin`
- `config_basic_rj45.json`

---

### 2. **rj45_to_automotive** - RJ45 to T1 Bridge
**Use Case:** Bridge RJ45 Ethernet to automotive T1 network

| Stream | Source | Destinations | VLAN | Description |
|--------|--------|--------------|------|-------------|
| 1 | P2A | P6, P7, P8, P9 | 100 | RJ45 to 4x T1 broadcast |
| 2 | P1 | P6, P7 | 200 | 100M to T1 pair |
| 3 | P3 | P8, P9, P10 | 300 | 1G to T1 triple |

**Files:**
- `sja1110_uc_rj45_to_automotive.bin`
- `sja1110_switch_rj45_to_automotive.bin`
- `config_rj45_to_automotive.json`

---

### 3. **redundant_gateway** - High Availability Gateway
**Use Case:** Redundant gateway with automatic failover

| Stream | Source | Destinations | VLAN | Priority | Description |
|--------|--------|--------------|------|----------|-------------|
| 1 | P2A | PFE, P6 | 100 | 6 | External to CPU with backup |
| 2 | PFE | P2A, P2B | 200 | 6 | CPU to dual external |
| 3 | P1 | P2A, P2B, P3, PFE | 10 | 7 | Critical control messages |

**Files:**
- `sja1110_uc_redundant_gateway.bin`
- `sja1110_switch_redundant_gateway.bin`
- `config_redundant_gateway.json`

---

### 4. **ring_topology** - Ring Network Redundancy
**Use Case:** Ring topology for network redundancy

| Stream | Source | Destinations | VLAN | Description |
|--------|--------|--------------|------|-------------|
| 1 | P2A | P2B, P6 | 100 | Ring input replication |
| 2 | P6 | P7, P8 | 200 | T1 ring segment |
| 3 | P8 | P1, P3 | 300 | Backup path |

**Files:**
- `sja1110_uc_ring_topology.bin`
- `sja1110_switch_ring_topology.bin`
- `config_ring_topology.json`

---

### 5. **load_balancing** - Traffic Load Distribution
**Use Case:** Distribute traffic load across multiple paths

| Stream | Source | Destinations | VLAN | Description |
|--------|--------|--------------|------|-------------|
| 1 | P2A | P1, P3, P6, P7 | 100 | High-speed distribution |
| 2 | P2B | PFE, P2A, P8, P9 | 200 | Premium replication |

**Files:**
- `sja1110_uc_load_balancing.bin`
- `sja1110_switch_load_balancing.bin`
- `config_load_balancing.json`

---

### 6. **mixed_automotive** - Automotive ECU Network
**Use Case:** Mixed automotive network with diagnostics

| Stream | Source | Destinations | VLAN | Priority | Description |
|--------|--------|--------------|------|----------|-------------|
| 1 | P1 | P6, P7, P8 | 100 | 6 | Diagnostic to ECUs |
| 2 | P6 | PFE, P2A | 200 | 6 | Sensor aggregation |
| 3 | PFE | P1-P8 (all) | 10 | 7 | Safety broadcast |

**Files:**
- `sja1110_uc_mixed_automotive.bin`
- `sja1110_switch_mixed_automotive.bin`
- `config_mixed_automotive.json`

---

### 7. **test_scenario** - Comprehensive Test Configuration
**Use Case:** Complete test setup for validation

| Stream | Source | Destinations | VLAN | Priority | Description |
|--------|--------|--------------|------|----------|-------------|
| 1 | PFE | P2A, P2B | 100 | 6 | CPU to external |
| 2 | P2A | P6, P7 | 200 | 6 | External to T1 |
| 3 | P6 | P7, P8 | 300 | 6 | T1 ring |
| 4 | P1 | P2A, P2B, P6 | 10 | 7 | Critical triple |

**Files:**
- `sja1110_uc_test_scenario.bin`
- `sja1110_switch_test_scenario.bin`
- `config_test_scenario.json`

---

### 8. **maximum_replication** - Maximum Port Replication
**Use Case:** Stress test with maximum replication

| Stream | Source | Destinations | VLAN | Priority | Description |
|--------|--------|--------------|------|----------|-------------|
| 1 | PFE | ALL (P1-P11) | 100 | 7 | Broadcast to all ports |
| 2 | P2A | ALL except P2A | 200 | 7 | Maximum fanout |

**Files:**
- `sja1110_uc_maximum_replication.bin`
- `sja1110_switch_maximum_replication.bin`
- `config_maximum_replication.json`

---

### 9. **dual_path** - Simple Dual Path
**Use Case:** Basic dual-path redundancy

| Stream | Source | Destinations | VLAN | Description |
|--------|--------|--------------|------|-------------|
| 1 | PFE | P2A, P2B | 100 | Primary dual path |
| 2 | P1 | P6, P7 | 200 | Secondary dual path |

**Files:**
- `sja1110_uc_dual_path.bin`
- `sja1110_switch_dual_path.bin`
- `config_dual_path.json`

---

### 10. **triple_redundancy** - Triple Redundancy
**Use Case:** Critical systems with triple redundancy

| Stream | Source | Destinations | VLAN | Priority | Description |
|--------|--------|--------------|------|----------|-------------|
| 1 | PFE | P2A, P2B, P3 | 10 | 7 | Critical triple 1 |
| 2 | P1 | P6, P7, P8 | 20 | 7 | Critical triple 2 |
| 3 | P2A | P9, P10, P11 | 30 | 7 | Critical triple 3 |

**Files:**
- `sja1110_uc_triple_redundancy.bin`
- `sja1110_switch_triple_redundancy.bin`
- `config_triple_redundancy.json`

---

## 🔧 Port Mapping Reference

| Port | Connector | Type | Speed | Description |
|------|-----------|------|-------|-------------|
| 0 | PFE | Internal | 1Gbps | S32G CPU interface |
| 1 | P1 | RJ45 | 100Mbps | 100BASE-TX |
| 2 | P2A | RJ45 | 1Gbps | 1000BASE-T |
| 3 | P2B | RJ45 | 1Gbps | 1000BASE-T |
| 4 | P3 | RJ45 | 1Gbps | 1000BASE-T |
| 5 | P6 | T1 | 100Mbps | 100BASE-T1 |
| 6 | P7 | T1 | 100Mbps | 100BASE-T1 |
| 7 | P8 | T1 | 100Mbps | 100BASE-T1 |
| 8 | P9 | T1 | 100Mbps | 100BASE-T1 |
| 9 | P10 | T1 | 100Mbps | 100BASE-T1 |
| 10 | P11 | T1 | 100Mbps | 100BASE-T1 |

## 📊 Scenario Selection Guide

| Requirement | Recommended Scenario | Key Features |
|-------------|---------------------|--------------|
| **Basic Testing** | `test_scenario` | 4 streams, all port types |
| **Simple Redundancy** | `dual_path` | 2-way replication |
| **High Availability** | `redundant_gateway` | Backup paths, priority |
| **Maximum Safety** | `triple_redundancy` | 3-way replication |
| **Automotive Bridge** | `rj45_to_automotive` | RJ45 to T1 conversion |
| **ECU Network** | `mixed_automotive` | Diagnostic + safety |
| **Stress Testing** | `maximum_replication` | All ports active |
| **Ring Networks** | `ring_topology` | Ring redundancy |
| **Load Distribution** | `load_balancing` | Traffic spreading |
| **Development** | `basic_rj45` | Simple setup |

## 🚀 Upload Instructions

### Method 1: Using Upload Script
```bash
cd binaries
./upload.sh <scenario_name>

# Examples:
./upload.sh test_scenario
./upload.sh triple_redundancy
./upload.sh maximum_replication
```

### Method 2: Direct Upload
```bash
sudo ./goldbox_dual_upload.sh \
  binaries/sja1110_uc_<scenario>.bin \
  binaries/sja1110_switch_<scenario>.bin
```

### Method 3: Master UC with Any Switch Config
```bash
# Use master UC binary with any switch configuration
sudo ./goldbox_dual_upload.sh \
  binaries/sja1110_uc_master.bin \
  binaries/sja1110_switch_<scenario>.bin
```

## 🧪 Testing and Verification

### Verify Replication
```bash
# Monitor replicated frames on destination ports
tcpdump -i sw0p2 -e -n &
tcpdump -i sw0p3 -e -n &

# Send test traffic
ping -I pfe0 192.168.1.100
```

### Check FRER Status
```bash
# View CB statistics
cat /sys/bus/spi/devices/spi0.0/switch-configuration/cb_stats

# Check port status
for i in {0..10}; do
  echo "Port $i: $(cat /sys/class/net/sw0p$i/carrier 2>/dev/null)"
done
```

### Verify R-TAG Headers
```bash
# Look for R-TAG EtherType (0xF1C1)
tcpdump -i sw0p2 -XX | grep -A2 "f1c1"
```

## 📝 Configuration Files

Each scenario includes a JSON configuration file with:
- Stream definitions
- Port mappings
- VLAN assignments
- Priority settings
- Binary file references

Example (`config_test_scenario.json`):
```json
{
  "scenario": "test_scenario",
  "description": "Comprehensive test configuration",
  "streams": [
    {
      "id": 1,
      "src_port": 0,
      "dst_ports": [2, 3],
      "vlan": 100,
      "name": "PFE_to_P2AB"
    }
  ],
  "uc_file": "sja1110_uc_test_scenario.bin",
  "switch_file": "sja1110_switch_test_scenario.bin"
}
```

## ⚠️ Important Notes

1. **Gold Box performs replication only** - Frame elimination must be configured on receiving devices
2. **Root privileges required** - Use `sudo` for upload commands
3. **Hardware specific** - These binaries are for NXP S32G-VNP-GLDBOX only
4. **VLAN separation** - Each stream uses unique VLAN ID
5. **Priority levels** - Critical traffic uses priority 7
6. **Sequence history** - Default 32 entries, video streams may need 64

## 📚 Additional Resources

- [FRER Configuration Guide](FRER_CONFIGURATION.md)
- [Port Test Script](port_test.sh)
- [Example Usage](frer_example.py)
- [IEEE 802.1CB Standard](https://standards.ieee.org/standard/802_1CB-2017.html)

## 🔄 Version Information

- **Tool Version:** 1.0.0
- **Binary Format:** SJA1110 Rev B
- **Generated:** 2024
- **Repository:** [github.com/hwkim3330/nxp-sja1110-control-tool](https://github.com/hwkim3330/nxp-sja1110-control-tool)

---

*For issues or questions, please open an issue on GitHub.*