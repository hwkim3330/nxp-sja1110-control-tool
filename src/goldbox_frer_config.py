#!/usr/bin/env python3
"""
Gold Box FRER Configuration with Actual Port Mapping
Based on S32G-VNP-GLDBOX Hardware Specification
"""

import struct
import json
import logging
import argparse
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import IntEnum
from datetime import datetime

# Gold Box Physical Port to SJA1110 Internal Port Mapping
class GoldBoxPort(IntEnum):
    """Gold Box Physical Port Mapping"""
    # External RJ45 Ports
    P1_100TX = 1      # 100BASE-TX RJ45 -> SJA1110 Port 1
    P2A_1000T = 2     # 1000BASE-T RJ45 -> SJA1110 Port 2 (via AR8035)
    P2B_1000T = 3     # 1000BASE-T RJ45 -> SJA1110 Port 3 (via AR8035)
    
    # Internal Connection
    PFE_MAC0 = 4      # S32G PFE_MAC0 -> SJA1110 Port 4 (SGMII)
    
    # 100BASE-T1 Automotive Ports (Mini50 connectors)
    P6_T1 = 5         # 100BASE-T1 -> SJA1110 Port 5
    P7_T1 = 6         # 100BASE-T1 -> SJA1110 Port 6
    P8_T1 = 7         # 100BASE-T1 -> SJA1110 Port 7
    P9_T1 = 8         # 100BASE-T1 -> SJA1110 Port 8
    P10_T1 = 9        # 100BASE-T1 -> SJA1110 Port 9
    P11_T1 = 10       # 100BASE-T1 -> SJA1110 Port 10
    
    # Direct S32G Connections (not through SJA1110)
    P3A_GMAC0 = 20    # 1000BASE-T -> S32G GMAC0 (not SJA1110)
    P3B_PFE2 = 21     # 1000BASE-T -> S32G PFE_MAC2 (not SJA1110)
    P5_PFE1 = 22      # 1000BASE-T -> S32G PFE_MAC1 (not SJA1110)

@dataclass
class FRERTestScenario:
    """FRER Test Scenario Definition"""
    name: str
    description: str
    input_port: int
    replicate_to: List[int]
    eliminate_at: Optional[int]
    vlan_id: int
    priority: int
    expected_behavior: str

class GoldBoxFRERConfig:
    """Gold Box FRER Configuration Generator"""
    
    # SJA1110 Configuration Memory Map
    DEVICE_ID = 0x000000
    GENERAL_PARAMS = 0x034000
    CB_CONFIG_BASE = 0x080000
    DPI_CONFIG_BASE = 0x0A0000
    VLAN_TABLE_BASE = 0x040000
    
    # CB Table Entry Sizes
    CB_SEQ_GEN_ENTRY_SIZE = 16
    CB_IND_REC_ENTRY_SIZE = 20
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_scenarios: List[FRERTestScenario] = []
        self.config_data = bytearray()
        
    def validate_port(self, port: int, port_name: str = "") -> bool:
        """Validate if port can be used in SJA1110"""
        # Ports 20-22 are direct S32G connections, not through SJA1110
        if port >= 20:
            self.logger.warning(f"{port_name} (port {port}) is directly connected to S32G, not through SJA1110")
            return False
        
        # Valid SJA1110 ports are 1-10 (Port 0 is reserved)
        if port < 1 or port > 10:
            self.logger.error(f"Invalid SJA1110 port: {port}")
            return False
            
        return True
    
    def add_test_scenario(self, scenario: FRERTestScenario):
        """Add FRER test scenario with validation"""
        # Validate input port
        if not self.validate_port(scenario.input_port, f"Input {scenario.name}"):
            raise ValueError(f"Invalid input port for scenario {scenario.name}")
        
        # Validate replication ports
        for port in scenario.replicate_to:
            if not self.validate_port(port, f"Replication {scenario.name}"):
                raise ValueError(f"Invalid replication port for scenario {scenario.name}")
        
        # Validate elimination port if specified
        if scenario.eliminate_at and not self.validate_port(scenario.eliminate_at, f"Elimination {scenario.name}"):
            raise ValueError(f"Invalid elimination port for scenario {scenario.name}")
        
        self.test_scenarios.append(scenario)
        self.logger.info(f"Added scenario: {scenario.name}")
    
    def create_pfe_to_external_redundancy(self):
        """Scenario 1: PFE to External Port Redundancy"""
        scenario = FRERTestScenario(
            name="PFE_to_P2AB",
            description="Traffic from PFE replicated to P2A and P2B for redundancy",
            input_port=GoldBoxPort.PFE_MAC0,
            replicate_to=[GoldBoxPort.P2A_1000T, GoldBoxPort.P2B_1000T],
            eliminate_at=None,  # Elimination at external device
            vlan_id=100,
            priority=7,
            expected_behavior="Frames from PFE_MAC0 duplicated to both P2A and P2B"
        )
        self.add_test_scenario(scenario)
    
    def create_external_to_pfe_redundancy(self):
        """Scenario 2: External to PFE with Redundancy"""
        scenario = FRERTestScenario(
            name="P2A_to_PFE",
            description="External traffic from P2A replicated through T1 ports, eliminated at PFE",
            input_port=GoldBoxPort.P2A_1000T,
            replicate_to=[GoldBoxPort.P6_T1, GoldBoxPort.P7_T1],
            eliminate_at=GoldBoxPort.PFE_MAC0,
            vlan_id=200,
            priority=6,
            expected_behavior="Frames from P2A sent through P6/P7, duplicates removed at PFE"
        )
        self.add_test_scenario(scenario)
    
    def create_t1_ring_redundancy(self):
        """Scenario 3: 100BASE-T1 Ring Redundancy"""
        scenario = FRERTestScenario(
            name="T1_Ring",
            description="100BASE-T1 ring redundancy for automotive applications",
            input_port=GoldBoxPort.P6_T1,
            replicate_to=[GoldBoxPort.P7_T1, GoldBoxPort.P8_T1],
            eliminate_at=GoldBoxPort.P10_T1,
            vlan_id=300,
            priority=5,
            expected_behavior="T1 traffic replicated through ring, eliminated at P10"
        )
        self.add_test_scenario(scenario)
    
    def create_critical_control_redundancy(self):
        """Scenario 4: Triple Redundancy for Critical Control"""
        scenario = FRERTestScenario(
            name="Critical_Control",
            description="Triple redundancy for safety-critical control messages",
            input_port=GoldBoxPort.P1_100TX,
            replicate_to=[GoldBoxPort.P2A_1000T, GoldBoxPort.P2B_1000T, GoldBoxPort.P6_T1],
            eliminate_at=GoldBoxPort.PFE_MAC0,
            vlan_id=10,
            priority=7,  # Highest priority
            expected_behavior="Critical messages triplicated, PFE receives single copy"
        )
        self.add_test_scenario(scenario)
    
    def generate_cb_config(self, scenario: FRERTestScenario) -> bytes:
        """Generate CB (Circuit Breaker) configuration for scenario"""
        config = bytearray()
        
        # CB Sequence Generation Entry (for replication)
        # Format: [stream_id:16][port_mask:16][flags:8][seq_num:16]
        stream_id = hash(scenario.name) & 0xFFFF
        
        # Create port mask for replication
        port_mask = 0
        for port in scenario.replicate_to:
            port_mask |= (1 << port)
        
        # Pack CB sequence generation entry
        config.extend(struct.pack('<HHxBH',
            stream_id,
            port_mask,
            0x80,  # Enable flag
            0      # Initial sequence number
        ))
        
        # CB Individual Recovery Entry (for elimination)
        if scenario.eliminate_at:
            # Format: [stream_id:16][port:8][flags:8][history:16][timeout:16]
            config.extend(struct.pack('<HBBHH',
                stream_id,
                scenario.eliminate_at,
                0x80,  # Enable flag
                32,    # History length
                100    # Reset timeout (ms)
            ))
        
        return bytes(config)
    
    def generate_dpi_config(self, scenario: FRERTestScenario) -> bytes:
        """Generate DPI (Deep Packet Inspection) configuration"""
        config = bytearray()
        
        stream_id = hash(scenario.name) & 0xFFFF
        
        # DPI Entry Format:
        # [stream_id:16][vlan_id:16][priority:8][ingress_port:8][flags:8]
        config.extend(struct.pack('<HHBBB',
            stream_id,
            scenario.vlan_id,
            scenario.priority,
            scenario.input_port,
            0x01  # CB_EN flag
        ))
        
        return bytes(config)
    
    def generate_switch_binary(self) -> bytes:
        """Generate complete sja1110_switch.bin"""
        self.config_data = bytearray()
        
        # Add header with valid marker
        self.config_data.extend(b'\x6A\xA6\x6A\xA6\x6A\xA6\x6A\xA6')
        
        # Device ID
        self.config_data.extend(struct.pack('<I', 0xB700030E))
        
        # Configuration flags
        config_flags = 0xF0000000  # All features enabled
        self.config_data.extend(struct.pack('<I', config_flags))
        
        # General Parameters
        self._add_general_params()
        
        # CB Configuration
        self._add_cb_config()
        
        # DPI Configuration
        self._add_dpi_config()
        
        # VLAN Configuration
        self._add_vlan_config()
        
        # Calculate CRC
        import zlib
        crc = zlib.crc32(bytes(self.config_data)) & 0xFFFFFFFF
        self.config_data.extend(struct.pack('<I', crc))
        
        return bytes(self.config_data)
    
    def _add_general_params(self):
        """Add general parameters section"""
        # Pad to general params offset
        while len(self.config_data) < self.GENERAL_PARAMS:
            self.config_data.append(0)
        
        # FRMREPEN (Frame Replication Enable)
        self.config_data.extend(struct.pack('<I', 1))
        
        # Host port (PFE_MAC0)
        self.config_data.append(GoldBoxPort.PFE_MAC0)
        
        # Cascade port (not used in single switch)
        self.config_data.append(0xFF)
    
    def _add_cb_config(self):
        """Add CB configuration for all scenarios"""
        # Pad to CB config offset
        while len(self.config_data) < self.CB_CONFIG_BASE:
            self.config_data.append(0)
        
        for scenario in self.test_scenarios:
            cb_config = self.generate_cb_config(scenario)
            self.config_data.extend(cb_config)
    
    def _add_dpi_config(self):
        """Add DPI configuration for all scenarios"""
        # Pad to DPI config offset
        while len(self.config_data) < self.DPI_CONFIG_BASE:
            self.config_data.append(0)
        
        for scenario in self.test_scenarios:
            dpi_config = self.generate_dpi_config(scenario)
            self.config_data.extend(dpi_config)
    
    def _add_vlan_config(self):
        """Add VLAN configuration"""
        # Pad to VLAN table offset
        while len(self.config_data) < self.VLAN_TABLE_BASE:
            self.config_data.append(0)
        
        # Add VLAN entries for each scenario
        for scenario in self.test_scenarios:
            # VLAN entry: [vlan_id:12][port_mask:11][flags:9]
            port_mask = (1 << scenario.input_port)
            for port in scenario.replicate_to:
                port_mask |= (1 << port)
            if scenario.eliminate_at:
                port_mask |= (1 << scenario.eliminate_at)
            
            vlan_entry = (scenario.vlan_id & 0xFFF) | ((port_mask & 0x7FF) << 12)
            self.config_data.extend(struct.pack('<I', vlan_entry))
    
    def save_config(self, filename: str = "goldbox_frer.bin"):
        """Save configuration to binary file"""
        config = self.generate_switch_binary()
        
        with open(filename, 'wb') as f:
            f.write(config)
        
        self.logger.info(f"Saved configuration to {filename} ({len(config)} bytes)")
        
        # Also save JSON for documentation
        self.save_test_plan(filename.replace('.bin', '_testplan.json'))
    
    def save_test_plan(self, filename: str):
        """Save test plan as JSON"""
        test_plan = {
            'timestamp': datetime.now().isoformat(),
            'device': 'S32G-VNP-GLDBOX',
            'switch': 'SJA1110A',
            'scenarios': []
        }
        
        for scenario in self.test_scenarios:
            test_plan['scenarios'].append({
                'name': scenario.name,
                'description': scenario.description,
                'input_port': f"Port {scenario.input_port} ({self._get_port_name(scenario.input_port)})",
                'replicate_to': [f"Port {p} ({self._get_port_name(p)})" for p in scenario.replicate_to],
                'eliminate_at': f"Port {scenario.eliminate_at} ({self._get_port_name(scenario.eliminate_at)})" if scenario.eliminate_at else "External device",
                'vlan_id': scenario.vlan_id,
                'priority': scenario.priority,
                'expected_behavior': scenario.expected_behavior
            })
        
        with open(filename, 'w') as f:
            json.dump(test_plan, f, indent=2)
        
        self.logger.info(f"Saved test plan to {filename}")
    
    def _get_port_name(self, port: int) -> str:
        """Get friendly name for port"""
        port_names = {
            1: "P1 (100BASE-TX)",
            2: "P2A (1000BASE-T)",
            3: "P2B (1000BASE-T)",
            4: "PFE_MAC0 (SGMII)",
            5: "P6 (100BASE-T1)",
            6: "P7 (100BASE-T1)",
            7: "P8 (100BASE-T1)",
            8: "P9 (100BASE-T1)",
            9: "P10 (100BASE-T1)",
            10: "P11 (100BASE-T1)"
        }
        return port_names.get(port, f"Unknown({port})")


def main():
    """Generate Gold Box FRER configuration"""
    parser = argparse.ArgumentParser(description='Gold Box FRER Configuration Generator')
    parser.add_argument('-o', '--output', default='goldbox_frer.bin',
                       help='Output binary file')
    parser.add_argument('-s', '--scenarios', nargs='+',
                       choices=['pfe_external', 'external_pfe', 't1_ring', 'critical'],
                       default=['pfe_external', 'external_pfe', 't1_ring', 'critical'],
                       help='Test scenarios to include')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create configuration
    config = GoldBoxFRERConfig()
    
    # Add selected scenarios
    if 'pfe_external' in args.scenarios:
        config.create_pfe_to_external_redundancy()
    
    if 'external_pfe' in args.scenarios:
        config.create_external_to_pfe_redundancy()
    
    if 't1_ring' in args.scenarios:
        config.create_t1_ring_redundancy()
    
    if 'critical' in args.scenarios:
        config.create_critical_control_redundancy()
    
    # Save configuration
    config.save_config(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("Gold Box FRER Configuration Summary")
    print("="*60)
    print(f"Output file: {args.output}")
    print(f"Test scenarios: {len(config.test_scenarios)}")
    print("\nScenarios configured:")
    for scenario in config.test_scenarios:
        print(f"  - {scenario.name}: {scenario.description}")
    print("\nPort Mapping Reference:")
    print("  P1: 100BASE-TX (Port 1)")
    print("  P2A/P2B: 1000BASE-T (Ports 2-3)")
    print("  PFE_MAC0: S32G Internal (Port 4)")
    print("  P6-P11: 100BASE-T1 (Ports 5-10)")
    print("="*60)


if __name__ == "__main__":
    main()