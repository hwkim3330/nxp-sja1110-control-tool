#!/usr/bin/env python3
"""
SJA1110 Firmware Builder
Generates firmware binaries for NXP Gold Box
"""

import struct
import json
import hashlib
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FirmwareHeader:
    """SJA1110 Firmware Header Structure"""
    magic: int = 0x53A11110  # 'SJA1110' signature
    version_major: int = 1
    version_minor: int = 0
    version_patch: int = 0
    header_size: int = 64
    payload_size: int = 0
    checksum: int = 0
    timestamp: int = 0
    config_offset: int = 0
    config_size: int = 0
    
    def to_bytes(self) -> bytes:
        """Convert header to binary format"""
        return struct.pack('>IHHHHIIIII',
                          self.magic,
                          self.version_major,
                          self.version_minor,
                          self.version_patch,
                          self.header_size,
                          self.payload_size,
                          self.checksum,
                          self.timestamp,
                          self.config_offset,
                          self.config_size)

class SJA1110FirmwareBuilder:
    """Build firmware binaries for SJA1110"""
    
    # Configuration sections
    GENERAL_CONFIG = 0x1000
    PORT_CONFIG = 0x2000
    VLAN_CONFIG = 0x3000
    QOS_CONFIG = 0x4000
    TSN_CONFIG = 0x5000
    FRER_CONFIG = 0x6000
    PTP_CONFIG = 0x7000
    SECURITY_CONFIG = 0x8000
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_sections: Dict[int, bytes] = {}
        self.metadata = {
            'build_time': datetime.now().isoformat(),
            'builder_version': '1.0.0',
            'target_device': 'SJA1110'
        }
    
    def add_general_config(self, config: Dict[str, Any]):
        """Add general switch configuration"""
        data = bytearray()
        
        # Switch mode (0=Unmanaged, 1=Managed)
        mode = 1 if config.get('managed', True) else 0
        data.extend(struct.pack('>I', mode))
        
        # Enable features
        features = 0
        if config.get('vlan_enable', True):
            features |= 0x01
        if config.get('qos_enable', True):
            features |= 0x02
        if config.get('tsn_enable', True):
            features |= 0x04
        if config.get('frer_enable', False):
            features |= 0x08
        if config.get('ptp_enable', True):
            features |= 0x10
        
        data.extend(struct.pack('>I', features))
        
        # MAC address
        mac = config.get('mac_address', '00:00:00:00:00:00')
        mac_bytes = bytes.fromhex(mac.replace(':', ''))
        data.extend(mac_bytes)
        
        # Padding
        data.extend(b'\x00' * (32 - len(data)))
        
        self.config_sections[self.GENERAL_CONFIG] = bytes(data)
        self.logger.info(f"Added general config: mode={mode}, features=0x{features:02X}")
    
    def add_port_config(self, ports: List[Dict[str, Any]]):
        """Add port configuration"""
        data = bytearray()
        
        # Number of ports
        data.extend(struct.pack('>H', len(ports)))
        
        for port in ports:
            port_id = port.get('id', 0)
            enabled = 1 if port.get('enabled', True) else 0
            speed = port.get('speed', 1000)  # Default 1Gbps
            duplex = 1 if port.get('duplex', 'full') == 'full' else 0
            auto_neg = 1 if port.get('auto_negotiation', True) else 0
            
            # Port configuration entry
            port_cfg = (port_id << 24) | (enabled << 16) | (auto_neg << 8) | duplex
            data.extend(struct.pack('>I', port_cfg))
            data.extend(struct.pack('>I', speed))
            
            # VLAN configuration for port
            pvid = port.get('pvid', 1)
            data.extend(struct.pack('>H', pvid))
            
            # Padding
            data.extend(b'\x00' * 6)
        
        self.config_sections[self.PORT_CONFIG] = bytes(data)
        self.logger.info(f"Added port config for {len(ports)} ports")
    
    def add_vlan_config(self, vlans: List[Dict[str, Any]]):
        """Add VLAN configuration"""
        data = bytearray()
        
        # Number of VLANs
        data.extend(struct.pack('>H', len(vlans)))
        
        for vlan in vlans:
            vlan_id = vlan.get('id', 1)
            name = vlan.get('name', f'VLAN{vlan_id}')[:16]
            ports = vlan.get('ports', [])
            
            # VLAN entry
            data.extend(struct.pack('>H', vlan_id))
            
            # Port membership bitmap
            port_mask = 0
            for port in ports:
                port_mask |= (1 << port)
            data.extend(struct.pack('>H', port_mask))
            
            # VLAN name (16 bytes)
            name_bytes = name.encode('utf-8')[:16]
            data.extend(name_bytes)
            data.extend(b'\x00' * (16 - len(name_bytes)))
        
        self.config_sections[self.VLAN_CONFIG] = bytes(data)
        self.logger.info(f"Added VLAN config for {len(vlans)} VLANs")
    
    def add_tsn_config(self, tsn: Dict[str, Any]):
        """Add TSN configuration"""
        data = bytearray()
        
        # TSN features
        features = 0
        if tsn.get('cbs_enable', False):
            features |= 0x01
        if tsn.get('tas_enable', False):
            features |= 0x02
        if tsn.get('preemption_enable', False):
            features |= 0x04
        
        data.extend(struct.pack('>I', features))
        
        # CBS configuration
        if tsn.get('cbs_enable', False):
            cbs = tsn.get('cbs', {})
            for tc in range(8):  # 8 traffic classes
                idle_slope = cbs.get(f'tc{tc}_idle_slope', 0)
                send_slope = cbs.get(f'tc{tc}_send_slope', 0)
                hi_credit = cbs.get(f'tc{tc}_hi_credit', 0)
                lo_credit = cbs.get(f'tc{tc}_lo_credit', 0)
                
                data.extend(struct.pack('>IIII', 
                                       idle_slope, send_slope, 
                                       hi_credit, lo_credit))
        
        # TAS configuration
        if tsn.get('tas_enable', False):
            tas = tsn.get('tas', {})
            cycle_time = tas.get('cycle_time_ns', 1000000)  # 1ms default
            data.extend(struct.pack('>Q', cycle_time))
            
            # Gate control list
            gcl = tas.get('gate_control_list', [])
            data.extend(struct.pack('>H', len(gcl)))
            
            for entry in gcl:
                gate_mask = entry.get('gate_mask', 0xFF)
                time_interval = entry.get('time_interval_ns', 125000)
                data.extend(struct.pack('>BQ', gate_mask, time_interval))
        
        self.config_sections[self.TSN_CONFIG] = bytes(data)
        self.logger.info(f"Added TSN config: features=0x{features:02X}")
    
    def add_frer_config(self, frer_binary: bytes):
        """Add FRER configuration from binary"""
        self.config_sections[self.FRER_CONFIG] = frer_binary
        self.logger.info(f"Added FRER config: {len(frer_binary)} bytes")
    
    def add_ptp_config(self, ptp: Dict[str, Any]):
        """Add PTP configuration"""
        data = bytearray()
        
        # PTP mode (0=Disabled, 1=OrdinaryClock, 2=BoundaryClock, 3=TransparentClock)
        mode = ptp.get('mode', 2)  # Default BoundaryClock
        data.extend(struct.pack('>I', mode))
        
        # PTP profile (0=Default, 1=Automotive, 2=Industrial)
        profile = ptp.get('profile', 1)  # Default Automotive
        data.extend(struct.pack('>I', profile))
        
        # Clock parameters
        priority1 = ptp.get('priority1', 128)
        priority2 = ptp.get('priority2', 128)
        domain = ptp.get('domain', 0)
        
        data.extend(struct.pack('>BBB', priority1, priority2, domain))
        
        # Padding
        data.extend(b'\x00' * 5)
        
        self.config_sections[self.PTP_CONFIG] = bytes(data)
        self.logger.info(f"Added PTP config: mode={mode}, profile={profile}")
    
    def build_firmware(self, output_file: str) -> str:
        """Build complete firmware binary"""
        # Create payload
        payload = bytearray()
        config_offsets = {}
        
        # Add configuration sections
        for section_id in sorted(self.config_sections.keys()):
            config_offsets[section_id] = len(payload)
            section_data = self.config_sections[section_id]
            
            # Section header
            payload.extend(struct.pack('>II', section_id, len(section_data)))
            payload.extend(section_data)
            
            # Align to 16-byte boundary
            padding = (16 - (len(payload) % 16)) % 16
            payload.extend(b'\x00' * padding)
        
        # Create header
        header = FirmwareHeader()
        header.timestamp = int(datetime.now().timestamp())
        header.payload_size = len(payload)
        header.config_offset = 64  # After header
        header.config_size = len(payload)
        
        # Calculate checksum
        checksum_data = header.to_bytes() + bytes(payload)
        header.checksum = struct.unpack('>I', hashlib.sha256(checksum_data).digest()[:4])[0]
        
        # Write firmware file
        with open(output_file, 'wb') as f:
            f.write(header.to_bytes())
            f.write(bytes(payload))
        
        # Write metadata
        meta_file = output_file.replace('.bin', '_meta.json')
        self.metadata['file_size'] = header.header_size + header.payload_size
        self.metadata['checksum'] = f"0x{header.checksum:08X}"
        self.metadata['sections'] = {
            hex(k): {'offset': v, 'size': len(self.config_sections[k])}
            for k, v in config_offsets.items()
        }
        
        with open(meta_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        self.logger.info(f"Built firmware: {output_file} ({header.payload_size + header.header_size} bytes)")
        return output_file
    
    def validate_firmware(self, firmware_file: str) -> bool:
        """Validate firmware file"""
        try:
            with open(firmware_file, 'rb') as f:
                # Read header
                header_data = f.read(64)
                if len(header_data) < 64:
                    self.logger.error(f"Header too short: {len(header_data)} bytes")
                    return False
                header = struct.unpack('>IHHHHIIIII', header_data[:32])
                
                magic = header[0]
                payload_size = header[5]
                stored_checksum = header[6]
                
                # Verify magic
                if magic != 0x53A11110:
                    self.logger.error(f"Invalid magic: 0x{magic:08X}")
                    return False
                
                # Read payload
                payload = f.read(payload_size)
                
                # Calculate checksum
                checksum_data = header_data[:24] + b'\x00\x00\x00\x00' + header_data[28:] + payload
                calculated_checksum = struct.unpack('>I', hashlib.sha256(checksum_data).digest()[:4])[0]
                
                if calculated_checksum != stored_checksum:
                    self.logger.error(f"Checksum mismatch: 0x{calculated_checksum:08X} != 0x{stored_checksum:08X}")
                    return False
                
                self.logger.info(f"Firmware validation successful: {firmware_file}")
                return True
                
        except Exception as e:
            self.logger.error(f"Firmware validation failed: {e}")
            return False


def create_example_firmware():
    """Create example firmware for Gold Box"""
    logging.basicConfig(level=logging.INFO)
    
    builder = SJA1110FirmwareBuilder()
    
    # General configuration
    builder.add_general_config({
        'managed': True,
        'vlan_enable': True,
        'qos_enable': True,
        'tsn_enable': True,
        'frer_enable': True,
        'ptp_enable': True,
        'mac_address': '00:04:9F:11:22:33'
    })
    
    # Port configuration (5 ports for SJA1110)
    ports = []
    for i in range(5):
        ports.append({
            'id': i,
            'enabled': True,
            'speed': 1000 if i < 4 else 100,  # Port 4 is 100BASE-T1
            'duplex': 'full',
            'auto_negotiation': True,
            'pvid': 1
        })
    builder.add_port_config(ports)
    
    # VLAN configuration
    vlans = [
        {'id': 1, 'name': 'Default', 'ports': [0, 1, 2, 3, 4]},
        {'id': 100, 'name': 'Control', 'ports': [0, 1, 2]},
        {'id': 200, 'name': 'Data', 'ports': [2, 3, 4]}
    ]
    builder.add_vlan_config(vlans)
    
    # TSN configuration
    builder.add_tsn_config({
        'cbs_enable': True,
        'tas_enable': True,
        'preemption_enable': False,
        'cbs': {
            'tc6_idle_slope': 75000,  # 75 Mbps for Class A
            'tc2_idle_slope': 75000,  # 75 Mbps for Class B
        },
        'tas': {
            'cycle_time_ns': 1000000,  # 1ms cycle
            'gate_control_list': [
                {'gate_mask': 0b11000000, 'time_interval_ns': 125000},  # TC7,6 open
                {'gate_mask': 0b00110000, 'time_interval_ns': 125000},  # TC5,4 open
                {'gate_mask': 0b00001100, 'time_interval_ns': 125000},  # TC3,2 open
                {'gate_mask': 0b00000011, 'time_interval_ns': 625000},  # TC1,0 open
            ]
        }
    })
    
    # Load FRER configuration
    try:
        with open('sja1110_frer.bin', 'rb') as f:
            frer_data = f.read()
            builder.add_frer_config(frer_data)
    except FileNotFoundError:
        # Create dummy FRER config if file doesn't exist
        builder.add_frer_config(b'\x00\x00\x00\x01')  # FRER enabled
    
    # PTP configuration
    builder.add_ptp_config({
        'mode': 2,  # Boundary Clock
        'profile': 1,  # Automotive profile
        'priority1': 128,
        'priority2': 128,
        'domain': 0
    })
    
    # Build firmware
    firmware_file = builder.build_firmware('sja1110_goldbox.bin')
    
    # Validate firmware
    if builder.validate_firmware(firmware_file):
        print(f"\nFirmware built successfully: {firmware_file}")
        print(f"Metadata saved to: {firmware_file.replace('.bin', '_meta.json')}")
    
    return firmware_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SJA1110 Firmware Builder')
    parser.add_argument('-c', '--config', help='Configuration JSON file')
    parser.add_argument('-o', '--output', default='sja1110_firmware.bin', 
                       help='Output firmware file')
    parser.add_argument('-v', '--validate', help='Validate firmware file')
    
    args = parser.parse_args()
    
    if args.validate:
        logging.basicConfig(level=logging.INFO)
        builder = SJA1110FirmwareBuilder()
        if builder.validate_firmware(args.validate):
            print("Firmware validation: PASSED")
        else:
            print("Firmware validation: FAILED")
    else:
        create_example_firmware()