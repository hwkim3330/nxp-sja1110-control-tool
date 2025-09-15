#!/usr/bin/env python3
"""
SJA1110 FRER (Frame Replication and Elimination for Reliability) Configuration
IEEE 802.1CB Implementation for TSN
"""

import struct
import json
import logging
from enum import IntEnum
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

class FRERFunction(IntEnum):
    """FRER Function Types"""
    SEQUENCE_GENERATION = 0x01
    SEQUENCE_RECOVERY = 0x02
    INDIVIDUAL_RECOVERY = 0x03
    SEQUENCE_ENCODE_DECODE = 0x04

class FRERAlgorithm(IntEnum):
    """FRER Recovery Algorithm"""
    VECTOR_RECOVERY = 0x00
    MATCH_RECOVERY = 0x01
    LATENT_ERROR_DETECTION = 0x02

@dataclass
class StreamIdentification:
    """Stream Identification Parameters"""
    stream_handle: int
    null_stream_id: bool = False
    source_mac: Optional[str] = None
    dest_mac: Optional[str] = None
    vlan_id: Optional[int] = None
    priority: Optional[int] = None
    
    def to_bytes(self) -> bytes:
        """Convert to binary format for firmware"""
        data = struct.pack('>H', self.stream_handle)
        flags = 0
        
        if self.null_stream_id:
            flags |= 0x01
        
        data += struct.pack('B', flags)
        
        if self.source_mac:
            mac_bytes = bytes.fromhex(self.source_mac.replace(':', ''))
            data += mac_bytes
        else:
            data += b'\x00' * 6
        
        if self.dest_mac:
            mac_bytes = bytes.fromhex(self.dest_mac.replace(':', ''))
            data += mac_bytes
        else:
            data += b'\x00' * 6
        
        vlan_priority = (self.vlan_id or 0) & 0xFFF
        if self.priority is not None:
            vlan_priority |= (self.priority << 13)
        
        data += struct.pack('>H', vlan_priority)
        
        return data

@dataclass
class SequenceGenerationEntry:
    """Sequence Generation Table Entry"""
    stream_handle: int
    port_mask: int  # Bitmask of ports for replication
    sequence_number: int = 0
    enable: bool = True
    
    def to_bytes(self) -> bytes:
        """Convert to binary format"""
        flags = 0x80 if self.enable else 0x00
        return struct.pack('>HBBH', 
                          self.stream_handle,
                          self.port_mask,
                          flags,
                          self.sequence_number)

@dataclass
class SequenceRecoveryEntry:
    """Sequence Recovery Table Entry"""
    stream_handle: int
    port: int
    sequence_number: int = 0
    history_length: int = 8
    reset_timeout: int = 100  # ms
    algorithm: FRERAlgorithm = FRERAlgorithm.VECTOR_RECOVERY
    enable: bool = True
    
    def to_bytes(self) -> bytes:
        """Convert to binary format"""
        flags = (0x80 if self.enable else 0x00) | (self.algorithm & 0x03)
        return struct.pack('>HBBHHH',
                          self.stream_handle,
                          self.port,
                          flags,
                          self.sequence_number,
                          self.history_length,
                          self.reset_timeout)

@dataclass
class FRERStatistics:
    """FRER Statistics Counters"""
    stream_handle: int
    passed_packets: int = 0
    discarded_packets: int = 0
    out_of_order_packets: int = 0
    rogue_packets: int = 0
    duplicate_packets: int = 0
    lost_packets: int = 0
    tagless_packets: int = 0
    resets: int = 0

class SJA1110FRER:
    """SJA1110 FRER Configuration Manager"""
    
    # FRER Table Offsets in Configuration
    STREAM_ID_TABLE_OFFSET = 0x040000
    SEQ_GEN_TABLE_OFFSET = 0x050000
    SEQ_REC_TABLE_OFFSET = 0x060000
    IND_REC_TABLE_OFFSET = 0x070000
    FRER_CONFIG_OFFSET = 0x080000
    
    MAX_STREAMS = 1024
    MAX_SEQUENCE_HISTORY = 32
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stream_identifications: Dict[int, StreamIdentification] = {}
        self.sequence_generation: Dict[int, SequenceGenerationEntry] = {}
        self.sequence_recovery: Dict[int, SequenceRecoveryEntry] = {}
        self.statistics: Dict[int, FRERStatistics] = {}
        
    def add_stream(self, stream_id: StreamIdentification):
        """Add stream identification entry"""
        if stream_id.stream_handle >= self.MAX_STREAMS:
            raise ValueError(f"Stream handle {stream_id.stream_handle} exceeds maximum {self.MAX_STREAMS}")
        
        self.stream_identifications[stream_id.stream_handle] = stream_id
        self.logger.info(f"Added stream {stream_id.stream_handle}: "
                        f"VLAN={stream_id.vlan_id}, Priority={stream_id.priority}")
    
    def configure_replication(self, stream_handle: int, egress_ports: List[int]):
        """
        Configure sequence generation (frame replication)
        
        Args:
            stream_handle: Stream identifier
            egress_ports: List of ports for frame replication
        """
        if stream_handle not in self.stream_identifications:
            raise ValueError(f"Stream {stream_handle} not defined")
        
        # Create port mask
        port_mask = 0
        for port in egress_ports:
            if port < 0 or port > 10:  # SJA1110 supports up to 11 ports
                raise ValueError(f"Invalid port number: {port}")
            port_mask |= (1 << port)
        
        entry = SequenceGenerationEntry(
            stream_handle=stream_handle,
            port_mask=port_mask,
            sequence_number=0,
            enable=True
        )
        
        self.sequence_generation[stream_handle] = entry
        self.logger.info(f"Configured replication for stream {stream_handle}: "
                        f"ports={egress_ports}, mask=0x{port_mask:04X}")
    
    def configure_elimination(self, stream_handle: int, ingress_port: int,
                            algorithm: FRERAlgorithm = FRERAlgorithm.VECTOR_RECOVERY,
                            history_length: int = 8,
                            reset_timeout: int = 100):
        """
        Configure sequence recovery (duplicate elimination)
        
        Args:
            stream_handle: Stream identifier
            ingress_port: Port for sequence recovery
            algorithm: Recovery algorithm
            history_length: Sequence history length
            reset_timeout: Reset timeout in milliseconds
        """
        if stream_handle not in self.stream_identifications:
            raise ValueError(f"Stream {stream_handle} not defined")
        
        if history_length > self.MAX_SEQUENCE_HISTORY:
            raise ValueError(f"History length {history_length} exceeds maximum {self.MAX_SEQUENCE_HISTORY}")
        
        entry = SequenceRecoveryEntry(
            stream_handle=stream_handle,
            port=ingress_port,
            sequence_number=0,
            history_length=history_length,
            reset_timeout=reset_timeout,
            algorithm=algorithm,
            enable=True
        )
        
        self.sequence_recovery[stream_handle] = entry
        self.logger.info(f"Configured elimination for stream {stream_handle}: "
                        f"port={ingress_port}, algorithm={algorithm.name}")
    
    def create_redundant_path(self, stream_handle: int, 
                             primary_path: List[int],
                             secondary_path: List[int],
                             dest_port: int):
        """
        Create redundant path configuration for FRER
        
        Args:
            stream_handle: Stream identifier
            primary_path: Primary path ports
            secondary_path: Secondary path ports
            dest_port: Destination port for elimination
        """
        # Configure replication at source
        replication_ports = list(set(primary_path[0:1] + secondary_path[0:1]))
        self.configure_replication(stream_handle, replication_ports)
        
        # Configure elimination at destination
        self.configure_elimination(stream_handle, dest_port)
        
        self.logger.info(f"Created redundant path for stream {stream_handle}: "
                        f"Primary={primary_path}, Secondary={secondary_path}, "
                        f"Destination={dest_port}")
    
    def generate_configuration(self) -> bytes:
        """Generate binary configuration for SJA1110"""
        config = bytearray()
        
        # Write FRER enable flag
        config.extend(struct.pack('>I', 0x00000001))  # FRER_EN = 1
        
        # Write stream identification table
        for handle, stream_id in sorted(self.stream_identifications.items()):
            config.extend(stream_id.to_bytes())
        
        # Pad to next section
        while len(config) < self.SEQ_GEN_TABLE_OFFSET:
            config.append(0)
        
        # Write sequence generation table
        for handle, seq_gen in sorted(self.sequence_generation.items()):
            config.extend(seq_gen.to_bytes())
        
        # Pad to next section
        while len(config) < self.SEQ_REC_TABLE_OFFSET:
            config.append(0)
        
        # Write sequence recovery table
        for handle, seq_rec in sorted(self.sequence_recovery.items()):
            config.extend(seq_rec.to_bytes())
        
        return bytes(config)
    
    def save_configuration(self, filename: str):
        """Save FRER configuration to binary file"""
        config = self.generate_configuration()
        
        with open(filename, 'wb') as f:
            f.write(config)
        
        self.logger.info(f"Saved FRER configuration to {filename} ({len(config)} bytes)")
    
    def save_json_config(self, filename: str):
        """Save configuration as JSON for documentation"""
        config = {
            'frer_enabled': True,
            'streams': [],
            'sequence_generation': [],
            'sequence_recovery': []
        }
        
        # Convert stream identifications
        for handle, stream_id in self.stream_identifications.items():
            config['streams'].append({
                'handle': handle,
                'source_mac': stream_id.source_mac,
                'dest_mac': stream_id.dest_mac,
                'vlan_id': stream_id.vlan_id,
                'priority': stream_id.priority
            })
        
        # Convert sequence generation
        for handle, seq_gen in self.sequence_generation.items():
            ports = []
            for i in range(11):
                if seq_gen.port_mask & (1 << i):
                    ports.append(i)
            
            config['sequence_generation'].append({
                'stream_handle': handle,
                'replication_ports': ports,
                'enabled': seq_gen.enable
            })
        
        # Convert sequence recovery
        for handle, seq_rec in self.sequence_recovery.items():
            config['sequence_recovery'].append({
                'stream_handle': handle,
                'ingress_port': seq_rec.port,
                'algorithm': seq_rec.algorithm.name,
                'history_length': seq_rec.history_length,
                'reset_timeout': seq_rec.reset_timeout,
                'enabled': seq_rec.enable
            })
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"Saved JSON configuration to {filename}")
    
    def get_statistics(self, stream_handle: int) -> FRERStatistics:
        """Get FRER statistics for a stream"""
        if stream_handle not in self.statistics:
            self.statistics[stream_handle] = FRERStatistics(stream_handle)
        
        return self.statistics[stream_handle]
    
    def reset_statistics(self, stream_handle: Optional[int] = None):
        """Reset FRER statistics"""
        if stream_handle is not None:
            if stream_handle in self.statistics:
                self.statistics[stream_handle] = FRERStatistics(stream_handle)
        else:
            # Reset all statistics
            for handle in self.statistics.keys():
                self.statistics[handle] = FRERStatistics(handle)
        
        self.logger.info(f"Reset statistics for {'all streams' if stream_handle is None else f'stream {stream_handle}'}")


def create_example_frer_config():
    """Create example FRER configuration for testing"""
    logging.basicConfig(level=logging.INFO)
    
    frer = SJA1110FRER()
    
    # Define critical control stream
    stream1 = StreamIdentification(
        stream_handle=1,
        source_mac="00:11:22:33:44:55",
        dest_mac="66:77:88:99:AA:BB",
        vlan_id=100,
        priority=7  # Highest priority
    )
    frer.add_stream(stream1)
    
    # Define sensor data stream
    stream2 = StreamIdentification(
        stream_handle=2,
        source_mac="AA:BB:CC:DD:EE:FF",
        dest_mac="11:22:33:44:55:66",
        vlan_id=200,
        priority=6
    )
    frer.add_stream(stream2)
    
    # Configure redundant paths
    # Stream 1: Port 0 -> Replicate to ports 1,2 -> Eliminate at port 3
    frer.create_redundant_path(
        stream_handle=1,
        primary_path=[0, 1, 3],
        secondary_path=[0, 2, 3],
        dest_port=3
    )
    
    # Stream 2: Port 4 -> Replicate to ports 5,6 -> Eliminate at port 7
    frer.create_redundant_path(
        stream_handle=2,
        primary_path=[4, 5, 7],
        secondary_path=[4, 6, 7],
        dest_port=7
    )
    
    # Save configurations
    frer.save_configuration("sja1110_frer.bin")
    frer.save_json_config("sja1110_frer_config.json")
    
    print("\nFRER Configuration Summary:")
    print(f"  Configured {len(frer.stream_identifications)} streams")
    print(f"  Configured {len(frer.sequence_generation)} replication points")
    print(f"  Configured {len(frer.sequence_recovery)} elimination points")
    
    return frer


if __name__ == "__main__":
    frer_config = create_example_frer_config()