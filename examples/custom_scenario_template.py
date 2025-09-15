#!/usr/bin/env python3
"""
Custom FRER Scenario Template

Use this template to create your own FRER configurations for specific use cases.
"""

import sys
import os
from typing import List, Dict

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sja1110_dual_firmware import SJA1110FirmwareBuilder

class CustomFRERScenario:
    """Template class for creating custom FRER scenarios"""
    
    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.builder = SJA1110FirmwareBuilder()
        
    def add_replication_rule(self, description: str, src_port: int, 
                           dst_ports: List[int], vlan_id: int = 100, 
                           priority: int = 6):
        """Add a replication rule to the scenario"""
        stream_id = len(self.builder.frer_streams) + 1
        
        self.builder.add_frer_replication_stream(
            stream_id=stream_id,
            src_port=src_port,
            dst_ports=dst_ports,
            vlan_id=vlan_id,
            priority=priority,
            name=f"{description}_{stream_id}"
        )
        
        print(f"Added rule: {description}")
        src_name = self.builder.port_config[src_port]['name']
        dst_names = [self.builder.port_config[p]['name'] for p in dst_ports]
        print(f"  {src_name} → {dst_names}")
        
    def build_and_save(self):
        """Build firmware and save files"""
        print(f"\nBuilding custom scenario: {self.scenario_name}")
        
        # Build firmware
        uc_firmware = self.builder.build_microcontroller_firmware()
        switch_config = self.builder.build_switch_firmware()
        
        # Generate filenames
        safe_name = self.scenario_name.lower().replace(' ', '_').replace('-', '_')
        uc_file = f"custom_{safe_name}_uc.bin"
        switch_file = f"custom_{safe_name}_switch.bin"
        
        # Save files
        with open(uc_file, 'wb') as f:
            f.write(uc_firmware)
        with open(switch_file, 'wb') as f:
            f.write(switch_config)
            
        # Save configuration
        self.builder.save_configuration_info(uc_file, switch_file)
        
        print(f"✓ Created {uc_file} ({len(uc_firmware):,} bytes)")
        print(f"✓ Created {switch_file} ({len(switch_config):,} bytes)")
        
        return uc_file, switch_file

def example_industrial_gateway():
    """Example: Industrial Gateway with Redundancy"""
    scenario = CustomFRERScenario("Industrial Gateway")
    
    # Rule 1: External network input with backup
    scenario.add_replication_rule(
        description="External_Network_Input",
        src_port=2,      # P2A (External network)
        dst_ports=[0, 5], # PFE + P6 (T1 backup)
        vlan_id=200,
        priority=7
    )
    
    # Rule 2: PFE output to dual RJ45
    scenario.add_replication_rule(
        description="PFE_to_Dual_Output",
        src_port=0,      # PFE
        dst_ports=[3, 4], # P2B, P3 (Dual outputs)
        vlan_id=201,
        priority=7
    )
    
    # Rule 3: Diagnostic port to T1 network
    scenario.add_replication_rule(
        description="Diagnostic_to_T1_Network", 
        src_port=1,      # P1 (Diagnostic)
        dst_ports=[5, 6, 7], # P6, P7, P8 (T1 network)
        vlan_id=202,
        priority=5
    )
    
    return scenario.build_and_save()

def example_automotive_ecu_hub():
    """Example: Automotive ECU Communication Hub"""
    scenario = CustomFRERScenario("Automotive ECU Hub")
    
    # Rule 1: Gateway to all ECUs
    scenario.add_replication_rule(
        description="Gateway_to_All_ECUs",
        src_port=2,      # P2A (Gateway)
        dst_ports=[5, 6, 7, 8, 9], # All T1 ports
        vlan_id=300,
        priority=7
    )
    
    # Rule 2: ECU sensor data aggregation
    scenario.add_replication_rule(
        description="ECU_Sensor_Data_Agg",
        src_port=5,      # P6 (Primary sensor ECU)
        dst_ports=[0, 2], # PFE + P2A (Data collection)
        vlan_id=301,
        priority=6
    )
    
    # Rule 3: Safety broadcast to all interfaces
    scenario.add_replication_rule(
        description="Safety_Broadcast_All",
        src_port=0,      # PFE (Safety controller)
        dst_ports=[1, 2, 3, 4, 8, 9, 10], # All external ports
        vlan_id=302,
        priority=7
    )
    
    return scenario.build_and_save()

def interactive_scenario_builder():
    """Interactive scenario builder"""
    print("\n🛠️  Interactive Custom Scenario Builder")
    print("=" * 50)
    
    scenario_name = input("Enter scenario name: ").strip()
    if not scenario_name:
        scenario_name = "Custom_Scenario"
    
    scenario = CustomFRERScenario(scenario_name)
    
    print("\nAvailable ports:")
    for port_id, info in scenario.builder.port_config.items():
        print(f"  {port_id}: {info['name']} ({info['type']})")
    
    while True:
        print(f"\nAdding replication rule #{len(scenario.builder.frer_streams) + 1}")
        
        # Get source port
        try:
            src_port = int(input("Source port (0-10): "))
            if src_port not in scenario.builder.port_config:
                print("Invalid source port!")
                continue
        except ValueError:
            print("Please enter a valid number!")
            continue
        
        # Get destination ports
        try:
            dst_input = input("Destination ports (comma-separated, e.g., 2,3,5): ")
            dst_ports = [int(p.strip()) for p in dst_input.split(',')]
            if not all(p in scenario.builder.port_config for p in dst_ports):
                print("One or more destination ports are invalid!")
                continue
        except ValueError:
            print("Please enter valid port numbers!")
            continue
        
        # Get description
        description = input("Rule description: ").strip()
        if not description:
            description = f"Rule_{len(scenario.builder.frer_streams) + 1}"
        
        # Get VLAN and priority (optional)
        vlan_id = 100 + len(scenario.builder.frer_streams)
        priority = 6
        
        try:
            vlan_input = input(f"VLAN ID (default: {vlan_id}): ").strip()
            if vlan_input:
                vlan_id = int(vlan_input)
                
            priority_input = input(f"Priority 0-7 (default: {priority}): ").strip()
            if priority_input:
                priority = int(priority_input)
                if not (0 <= priority <= 7):
                    print("Priority must be 0-7, using default")
                    priority = 6
        except ValueError:
            print("Using default values")
        
        # Add the rule
        scenario.add_replication_rule(description, src_port, dst_ports, vlan_id, priority)
        
        # Continue?
        if input("\nAdd another rule? (y/N): ").lower().strip() != 'y':
            break
    
    # Build and save
    return scenario.build_and_save()

def main():
    """Main function - demonstrates different ways to create custom scenarios"""
    print("NXP SJA1110 Custom FRER Scenario Builder")
    print("=" * 50)
    
    print("\nAvailable examples:")
    print("1. Industrial Gateway with Redundancy")
    print("2. Automotive ECU Communication Hub") 
    print("3. Interactive Scenario Builder")
    print("4. Exit")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            uc_file, switch_file = example_industrial_gateway()
        elif choice == '2':
            uc_file, switch_file = example_automotive_ecu_hub()
        elif choice == '3':
            uc_file, switch_file = interactive_scenario_builder()
        elif choice == '4':
            print("Exiting...")
            return
        else:
            print("Invalid choice!")
            return
        
        print(f"\n✅ Custom scenario created successfully!")
        print(f"\nUpload with:")
        print(f"  sudo ./goldbox_dual_upload.sh {uc_file} {switch_file}")
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()