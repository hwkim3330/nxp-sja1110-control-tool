#!/usr/bin/env python3
"""
Quick Start Example for NXP SJA1110 FRER Configuration

This example shows how to quickly create and upload a basic FRER configuration
for RJ45 port replication on the Gold Box.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sja1110_dual_firmware import SJA1110FirmwareBuilder

def create_basic_rj45_frer():
    """Create a basic RJ45 replication scenario"""
    print("Creating basic RJ45 FRER configuration...")
    
    # Create firmware builder
    builder = SJA1110FirmwareBuilder()
    
    # Add a simple replication stream: P2A -> P2B, P3
    builder.add_frer_replication_stream(
        stream_id=1,
        src_port=2,         # P2A (1G RJ45)
        dst_ports=[3, 4],   # P2B, P3 (1G RJ45)
        vlan_id=100,
        priority=7,
        name="P2A_to_P2B_P3_Basic"
    )
    
    # Add reverse path: P1 -> P2A
    builder.add_frer_replication_stream(
        stream_id=2,
        src_port=1,         # P1 (100M RJ45)
        dst_ports=[2],      # P2A (1G RJ45)
        vlan_id=101,
        priority=6,
        name="P1_to_P2A_Uplink"
    )
    
    # Build firmware
    print("Building firmware binaries...")
    uc_firmware = builder.build_microcontroller_firmware()
    switch_config = builder.build_switch_firmware()
    
    # Save files
    uc_file = 'example_sja1110_uc.bin'
    switch_file = 'example_sja1110_switch.bin'
    
    with open(uc_file, 'wb') as f:
        f.write(uc_firmware)
    print(f"✓ Created {uc_file} ({len(uc_firmware):,} bytes)")
    
    with open(switch_file, 'wb') as f:
        f.write(switch_config)
    print(f"✓ Created {switch_file} ({len(switch_config):,} bytes)")
    
    # Save configuration info
    builder.save_configuration_info(uc_file, switch_file)
    print("✓ Configuration details saved to sja1110_firmware_config.json")
    
    print("\nFRER Configuration Summary:")
    for stream in builder.frer_streams:
        src_name = builder.port_config[stream['src_port']]['name']
        dst_names = [builder.port_config[p]['name'] for p in stream['dst_ports']]
        print(f"  • {stream['name']}")
        print(f"    {src_name} → {dst_names}")
        print(f"    VLAN: {stream['vlan_id']}, Priority: {stream['priority']}")
    
    return uc_file, switch_file

def show_upload_instructions(uc_file, switch_file):
    """Show upload instructions"""
    print("\n" + "="*60)
    print("Upload Instructions")
    print("="*60)
    print(f"1. Copy files to Gold Box:")
    print(f"   sudo cp {uc_file} {switch_file} /lib/firmware/")
    print()
    print(f"2. Or use the upload script:")
    print(f"   sudo ./goldbox_dual_upload.sh {uc_file} {switch_file}")
    print()
    print(f"3. Verify upload:")
    print(f"   cat /sys/bus/spi/devices/spi0.0/device_id")
    print()
    print(f"4. Test FRER functionality:")
    print(f"   # Connect cables to P2A (input) and P2B/P3 (outputs)")
    print(f"   # Send traffic to P2A and verify replication on P2B and P3")
    print(f"   tcpdump -i sw0p3 -v &")
    print(f"   tcpdump -i sw0p4 -v &")
    print(f"   # Send test traffic from external device to P2A")

def main():
    """Main function"""
    print("NXP SJA1110 FRER Quick Start Example")
    print("=" * 50)
    
    try:
        # Create basic FRER configuration
        uc_file, switch_file = create_basic_rj45_frer()
        
        # Show upload instructions
        show_upload_instructions(uc_file, switch_file)
        
        print("\n✅ Quick start example completed successfully!")
        print("📖 See README.md for more detailed instructions and advanced scenarios.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()