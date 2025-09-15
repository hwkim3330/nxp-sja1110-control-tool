#!/usr/bin/env python3
"""
Generate all FRER binary configurations for Gold Box
Creates UC and Switch binaries for all scenarios
"""

import os
import sys
import struct
import zlib
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Constants
IMAGE_VALID_MARKER = b'\x6A\xA6\x6A\xA6\x6A\xA6\x6A\xA6'
DEVICE_ID_SJA1110 = 0xb700030e
RTAG_ETHERTYPE = 0xF1C1

# Binary sizes
UC_BINARY_SIZE = 320280
SWITCH_BINARY_SIZE = 655360

def generate_uc_binary(scenario_name):
    """Generate UC binary for a scenario"""
    uc_data = bytearray()
    uc_data.extend(IMAGE_VALID_MARKER)
    uc_data.extend(struct.pack('<I', DEVICE_ID_SJA1110))

    # Add scenario identifier
    scenario_id = scenario_name.encode('utf-8')[:32]
    uc_data.extend(scenario_id)
    uc_data.extend(b'\x00' * (32 - len(scenario_id)))

    # Pad to expected size
    while len(uc_data) < UC_BINARY_SIZE:
        uc_data.extend(b'\x00')

    return bytes(uc_data)

def generate_switch_binary(streams):
    """Generate switch binary with FRER configuration"""
    config = bytearray()

    # Header
    config.extend(IMAGE_VALID_MARKER)
    config.extend(struct.pack('<I', DEVICE_ID_SJA1110))

    # Configuration flags
    config_flags = (1 << 31) | (1 << 30) | (1 << 29) | (1 << 28)
    config.extend(struct.pack('<I', config_flags))

    # Pad to General Parameters offset (0x034000)
    while len(config) < 0x034000:
        config.extend(b'\x00')

    # General Parameters - FRMREPEN (Frame Replication Enable)
    config.extend(struct.pack('<I', 1))  # Enable FRER
    config.extend(struct.pack('<BB', 0, 10))  # Host port 0, Cascade port 10

    # Pad to CB Sequence Generation Table (0x080000)
    while len(config) < 0x080000:
        config.extend(b'\x00')

    # CB Sequence Generation Table (for frame replication)
    for stream in streams:
        # Calculate port mask
        port_mask = sum(1 << p for p in stream['dst_ports'])

        cb_entry = struct.pack('<HHBH',
                              stream['id'],      # stream_handle
                              port_mask,         # port_mask
                              0x80,             # flags (enabled)
                              0)                # seq_num
        config.extend(cb_entry)

    # Pad to CB Individual Recovery Table (0x090000)
    while len(config) < 0x090000:
        config.extend(b'\x00')

    # CB Individual Recovery Table (for duplicate elimination)
    for stream in streams:
        rec_entry = struct.pack('<HBBHHH',
                               stream['id'],       # stream_handle
                               stream['src_port'], # ingress_port
                               0x80,              # flags (enabled)
                               0,                 # seq_num
                               32,                # history_len
                               100)               # reset_timeout
        config.extend(rec_entry)

    # Pad to DPI Table (0x0A0000)
    while len(config) < 0x0A0000:
        config.extend(b'\x00')

    # DPI Configuration
    for stream in streams:
        dpi_entry = struct.pack('<HHHBBBB',
                               stream['id'],           # stream_id
                               stream.get('vlan', 100), # vlan_id
                               RTAG_ETHERTYPE,         # rtag_type
                               1,                      # cb_en
                               1,                      # sn_num_greater
                               stream.get('priority', 6), # priority
                               stream['src_port'])     # ingress_port
        config.extend(dpi_entry)

    # Pad to minimum size
    while len(config) < SWITCH_BINARY_SIZE:
        config.extend(b'\x00')

    # Add CRC32
    crc = zlib.crc32(bytes(config)) & 0xFFFFFFFF
    config.extend(struct.pack('<I', crc))

    return bytes(config)

def main():
    """Generate all FRER binaries"""

    # Port mapping
    port_map = {
        'PFE': 0, 'P1': 1, 'P2A': 2, 'P2B': 3, 'P3': 4,
        'P6': 5, 'P7': 6, 'P8': 7, 'P9': 8, 'P10': 9, 'P11': 10
    }

    # Define all scenarios
    scenarios = {
        'basic_rj45': {
            'description': 'Basic RJ45 frame replication',
            'streams': [
                {'id': 1, 'src_port': 1, 'dst_ports': [2, 3], 'vlan': 100, 'name': 'P1_to_P2AB'},
                {'id': 2, 'src_port': 2, 'dst_ports': [1, 4], 'vlan': 200, 'name': 'P2A_to_P1P3'},
            ]
        },
        'rj45_to_automotive': {
            'description': 'RJ45 to T1 automotive network bridge',
            'streams': [
                {'id': 1, 'src_port': 2, 'dst_ports': [5, 6, 7, 8], 'vlan': 100, 'name': 'P2A_to_T1'},
                {'id': 2, 'src_port': 1, 'dst_ports': [5, 6], 'vlan': 200, 'name': 'P1_to_T1_pair'},
                {'id': 3, 'src_port': 4, 'dst_ports': [7, 8, 9], 'vlan': 300, 'name': 'P3_to_T1_triple'},
            ]
        },
        'redundant_gateway': {
            'description': 'Redundant gateway with backup paths',
            'streams': [
                {'id': 1, 'src_port': 2, 'dst_ports': [0, 5], 'vlan': 100, 'name': 'External_to_PFE'},
                {'id': 2, 'src_port': 0, 'dst_ports': [2, 3], 'vlan': 200, 'name': 'PFE_to_External'},
                {'id': 3, 'src_port': 1, 'dst_ports': [2, 3, 4, 0], 'vlan': 10, 'priority': 7, 'name': 'Control_Critical'},
            ]
        },
        'ring_topology': {
            'description': 'Ring topology for redundancy',
            'streams': [
                {'id': 1, 'src_port': 2, 'dst_ports': [3, 5], 'vlan': 100, 'name': 'Ring_In'},
                {'id': 2, 'src_port': 5, 'dst_ports': [6, 7], 'vlan': 200, 'name': 'T1_Ring'},
                {'id': 3, 'src_port': 7, 'dst_ports': [1, 4], 'vlan': 300, 'name': 'Backup_Path'},
            ]
        },
        'load_balancing': {
            'description': 'Traffic load balancing',
            'streams': [
                {'id': 1, 'src_port': 2, 'dst_ports': [1, 4, 5, 6], 'vlan': 100, 'name': 'High_Speed_Distribution'},
                {'id': 2, 'src_port': 3, 'dst_ports': [0, 2, 7, 8], 'vlan': 200, 'name': 'Premium_Replication'},
            ]
        },
        'mixed_automotive': {
            'description': 'Mixed automotive ECU network',
            'streams': [
                {'id': 1, 'src_port': 1, 'dst_ports': [5, 6, 7], 'vlan': 100, 'name': 'Diagnostic_to_ECU'},
                {'id': 2, 'src_port': 5, 'dst_ports': [0, 2], 'vlan': 200, 'name': 'Sensor_Aggregation'},
                {'id': 3, 'src_port': 0, 'dst_ports': [1, 2, 3, 4, 5, 6, 7, 8], 'vlan': 10, 'priority': 7, 'name': 'Safety_Broadcast'},
            ]
        },
        'test_scenario': {
            'description': 'Comprehensive test configuration',
            'streams': [
                {'id': 1, 'src_port': 0, 'dst_ports': [2, 3], 'vlan': 100, 'name': 'PFE_to_P2AB'},
                {'id': 2, 'src_port': 2, 'dst_ports': [5, 6], 'vlan': 200, 'name': 'P2A_to_PFE'},
                {'id': 3, 'src_port': 5, 'dst_ports': [6, 7], 'vlan': 300, 'name': 'T1_Ring'},
                {'id': 4, 'src_port': 1, 'dst_ports': [2, 3, 5], 'vlan': 10, 'priority': 7, 'name': 'Critical_Triple'},
            ]
        },
        'maximum_replication': {
            'description': 'Maximum replication test (all ports)',
            'streams': [
                {'id': 1, 'src_port': 0, 'dst_ports': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'vlan': 100, 'priority': 7, 'name': 'PFE_to_ALL'},
                {'id': 2, 'src_port': 2, 'dst_ports': [0, 1, 3, 4, 5, 6, 7, 8, 9, 10], 'vlan': 200, 'priority': 7, 'name': 'P2A_to_ALL'},
            ]
        },
        'dual_path': {
            'description': 'Simple dual path redundancy',
            'streams': [
                {'id': 1, 'src_port': 0, 'dst_ports': [2, 3], 'vlan': 100, 'name': 'Primary_Dual'},
                {'id': 2, 'src_port': 1, 'dst_ports': [5, 6], 'vlan': 200, 'name': 'Secondary_Dual'},
            ]
        },
        'triple_redundancy': {
            'description': 'Triple redundancy for critical systems',
            'streams': [
                {'id': 1, 'src_port': 0, 'dst_ports': [2, 3, 4], 'vlan': 10, 'priority': 7, 'name': 'Critical_Triple_1'},
                {'id': 2, 'src_port': 1, 'dst_ports': [5, 6, 7], 'vlan': 20, 'priority': 7, 'name': 'Critical_Triple_2'},
                {'id': 3, 'src_port': 2, 'dst_ports': [8, 9, 10], 'vlan': 30, 'priority': 7, 'name': 'Critical_Triple_3'},
            ]
        }
    }

    output_dir = '/home/kim/nxp-sja1110-control-tool/binaries'

    print("=" * 60)
    print("Generating FRER Binaries for Gold Box")
    print("=" * 60)

    # Generate binaries for each scenario
    for scenario_name, scenario_data in scenarios.items():
        print(f"\nGenerating: {scenario_name}")
        print(f"  Description: {scenario_data['description']}")
        print(f"  Streams: {len(scenario_data['streams'])}")

        # Generate UC binary
        uc_binary = generate_uc_binary(scenario_name)
        uc_filename = os.path.join(output_dir, f"sja1110_uc_{scenario_name}.bin")
        with open(uc_filename, 'wb') as f:
            f.write(uc_binary)
        print(f"  ✓ UC binary: {os.path.basename(uc_filename)} ({len(uc_binary)} bytes)")

        # Generate switch binary
        switch_binary = generate_switch_binary(scenario_data['streams'])
        switch_filename = os.path.join(output_dir, f"sja1110_switch_{scenario_name}.bin")
        with open(switch_filename, 'wb') as f:
            f.write(switch_binary)
        print(f"  ✓ Switch binary: {os.path.basename(switch_filename)} ({len(switch_binary)} bytes)")

        # Generate JSON configuration
        config = {
            'scenario': scenario_name,
            'description': scenario_data['description'],
            'streams': scenario_data['streams'],
            'uc_file': os.path.basename(uc_filename),
            'switch_file': os.path.basename(switch_filename)
        }
        json_filename = os.path.join(output_dir, f"config_{scenario_name}.json")
        with open(json_filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"  ✓ Config JSON: {os.path.basename(json_filename)}")

    # Generate master UC binary (works with all switch configs)
    master_uc = generate_uc_binary('master')
    master_uc_file = os.path.join(output_dir, 'sja1110_uc_master.bin')
    with open(master_uc_file, 'wb') as f:
        f.write(master_uc)
    print(f"\n✓ Master UC binary: sja1110_uc_master.bin")

    # Create upload script
    upload_script = os.path.join(output_dir, 'upload.sh')
    with open(upload_script, 'w') as f:
        f.write("""#!/bin/bash
# Upload script for FRER binaries
SCENARIO="${1:-test_scenario}"
echo "Uploading scenario: $SCENARIO"
sudo ../goldbox_dual_upload.sh sja1110_uc_${SCENARIO}.bin sja1110_switch_${SCENARIO}.bin
""")
    os.chmod(upload_script, 0o755)

    print("\n" + "=" * 60)
    print("All binaries generated successfully!")
    print(f"Location: {output_dir}")
    print("\nUsage:")
    print("  cd binaries")
    print("  ./upload.sh <scenario_name>")
    print("\nAvailable scenarios:")
    for name in scenarios.keys():
        print(f"  - {name}")
    print("=" * 60)

if __name__ == "__main__":
    main()