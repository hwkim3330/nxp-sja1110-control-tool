#!/usr/bin/env python3
"""
NXP SJA1110 Ethernet Switch Driver
Supports SPI and I2C communication interfaces
"""

try:
    import spidev
except ImportError:
    spidev = None
    
try:
    import smbus2
except ImportError:
    smbus2 = None
import struct
import time
import logging
from enum import IntEnum
from typing import Optional, Union, List, Dict, Any

# SJA1110 Register Definitions
class SJA1110Registers(IntEnum):
    # Device ID and Configuration
    DEVICE_ID = 0x000000
    SWITCH_CFG = 0x020000
    PORT_STATUS_0 = 0x030000
    PORT_STATUS_1 = 0x030004
    PORT_STATUS_2 = 0x030008
    PORT_STATUS_3 = 0x03000C
    PORT_STATUS_4 = 0x030010
    
    # MAC Configuration Table
    MAC_CONFIG_TABLE = 0x040000
    VLAN_LOOKUP_TABLE = 0x050000
    L2_FORWARDING_TABLE = 0x060000
    
    # TSN Configuration
    CBS_CONFIG = 0x080000  # Credit-Based Shaper
    TAS_CONFIG = 0x090000  # Time-Aware Shaper
    PTP_CONFIG = 0x0A0000  # Precision Time Protocol
    
    # Statistics
    STATS_PORT_0 = 0x200000
    STATS_PORT_1 = 0x210000
    STATS_PORT_2 = 0x220000
    STATS_PORT_3 = 0x230000
    STATS_PORT_4 = 0x240000
    
    # General Parameters
    GENERAL_PARAMS = 0x100000
    CLOCK_CONFIG = 0x110000
    RESET_CTRL = 0x120000

class SJA1110Driver:
    """Driver for NXP SJA1110 TSN Ethernet Switch"""
    
    def __init__(self, interface: str = "spi", **kwargs):
        """
        Initialize SJA1110 driver
        
        Args:
            interface: Communication interface ('spi' or 'i2c')
            **kwargs: Interface-specific parameters
                For SPI: bus=0, device=0, max_speed=10000000
                For I2C: bus=1, address=0x48
        """
        self.interface = interface.lower()
        self.logger = logging.getLogger(__name__)
        
        if self.interface == "spi":
            self._init_spi(kwargs.get('bus', 0), 
                          kwargs.get('device', 0),
                          kwargs.get('max_speed', 10000000))
        elif self.interface == "i2c":
            self._init_i2c(kwargs.get('bus', 1),
                          kwargs.get('address', 0x48))
        else:
            raise ValueError(f"Unsupported interface: {interface}")
        
        self._verify_device()
    
    def _init_spi(self, bus: int, device: int, max_speed: int):
        """Initialize SPI interface"""
        if spidev is None:
            raise ImportError("spidev module not installed. Install with: pip3 install spidev")
        try:
            self.spi = spidev.SpiDev()
            self.spi.open(bus, device)
            self.spi.max_speed_hz = max_speed
            self.spi.mode = 0b00  # SPI Mode 0
            self.spi.bits_per_word = 8
            self.logger.info(f"SPI initialized: bus={bus}, device={device}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SPI: {e}")
            raise
    
    def _init_i2c(self, bus: int, address: int):
        """Initialize I2C interface"""
        if smbus2 is None:
            raise ImportError("smbus2 module not installed. Install with: pip3 install smbus2")
        try:
            self.i2c_bus = smbus2.SMBus(bus)
            self.i2c_address = address
            self.logger.info(f"I2C initialized: bus={bus}, address=0x{address:02X}")
        except Exception as e:
            self.logger.error(f"Failed to initialize I2C: {e}")
            raise
    
    def _verify_device(self):
        """Verify device ID"""
        device_id = self.read_register(SJA1110Registers.DEVICE_ID)
        expected_id = 0x9F70030  # SJA1110 Device ID
        
        if device_id != expected_id:
            self.logger.warning(f"Unexpected device ID: 0x{device_id:08X} "
                              f"(expected 0x{expected_id:08X})")
        else:
            self.logger.info(f"SJA1110 detected: ID=0x{device_id:08X}")
    
    def read_register(self, address: int, length: int = 4) -> int:
        """
        Read from SJA1110 register
        
        Args:
            address: Register address
            length: Number of bytes to read (default 4)
        
        Returns:
            Register value
        """
        if self.interface == "spi":
            return self._spi_read(address, length)
        else:
            return self._i2c_read(address, length)
    
    def write_register(self, address: int, value: int, length: int = 4):
        """
        Write to SJA1110 register
        
        Args:
            address: Register address
            value: Value to write
            length: Number of bytes to write (default 4)
        """
        if self.interface == "spi":
            self._spi_write(address, value, length)
        else:
            self._i2c_write(address, value, length)
    
    def _spi_read(self, address: int, length: int) -> int:
        """SPI read operation"""
        # SJA1110 SPI protocol: [CMD][ADDR][DATA]
        cmd = 0x00  # Read command
        addr_bytes = [(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        
        tx_data = [cmd] + addr_bytes + [0x00] * length
        rx_data = self.spi.xfer2(tx_data)
        
        # Extract data from response
        value = 0
        for i in range(length):
            value = (value << 8) | rx_data[4 + i]
        
        return value
    
    def _spi_write(self, address: int, value: int, length: int):
        """SPI write operation"""
        # SJA1110 SPI protocol: [CMD][ADDR][DATA]
        cmd = 0x80  # Write command
        addr_bytes = [(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        
        data_bytes = []
        for i in range(length):
            data_bytes.append((value >> (8 * (length - 1 - i))) & 0xFF)
        
        tx_data = [cmd] + addr_bytes + data_bytes
        self.spi.xfer2(tx_data)
    
    def _i2c_read(self, address: int, length: int) -> int:
        """I2C read operation"""
        # Send register address
        addr_bytes = [(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        
        with smbus2.SMBus(self.i2c_bus.bus) as bus:
            # Write register address
            bus.write_i2c_block_data(self.i2c_address, addr_bytes[0], addr_bytes[1:])
            
            # Read data
            data = bus.read_i2c_block_data(self.i2c_address, 0, length)
        
        # Convert to integer
        value = 0
        for byte in data:
            value = (value << 8) | byte
        
        return value
    
    def _i2c_write(self, address: int, value: int, length: int):
        """I2C write operation"""
        # Prepare address and data
        addr_bytes = [(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        
        data_bytes = []
        for i in range(length):
            data_bytes.append((value >> (8 * (length - 1 - i))) & 0xFF)
        
        with smbus2.SMBus(self.i2c_bus.bus) as bus:
            # Write register address and data
            bus.write_i2c_block_data(self.i2c_address, addr_bytes[0], 
                                    addr_bytes[1:] + data_bytes)
    
    def reset(self):
        """Reset the switch"""
        self.logger.info("Resetting SJA1110...")
        self.write_register(SJA1110Registers.RESET_CTRL, 0x01)
        time.sleep(0.5)  # Wait for reset to complete
        self._verify_device()
    
    def get_port_status(self, port: int) -> Dict[str, Any]:
        """
        Get status of a specific port
        
        Args:
            port: Port number (0-4)
        
        Returns:
            Dictionary with port status information
        """
        if port < 0 or port > 4:
            raise ValueError(f"Invalid port number: {port}")
        
        status_reg = SJA1110Registers.PORT_STATUS_0 + (port * 4)
        status = self.read_register(status_reg)
        
        return {
            'port': port,
            'link_up': bool(status & 0x01),
            'speed': self._decode_speed((status >> 1) & 0x03),
            'duplex': 'full' if (status & 0x08) else 'half',
            'auto_neg': bool(status & 0x10),
            'flow_control': bool(status & 0x20)
        }
    
    def _decode_speed(self, speed_bits: int) -> str:
        """Decode speed bits to string"""
        speeds = {0: '10Mbps', 1: '100Mbps', 2: '1Gbps', 3: '2.5Gbps'}
        return speeds.get(speed_bits, 'unknown')
    
    def configure_vlan(self, vlan_id: int, ports: List[int], tagged: bool = True):
        """
        Configure VLAN
        
        Args:
            vlan_id: VLAN ID (1-4094)
            ports: List of port numbers to include
            tagged: Whether ports should be tagged
        """
        if vlan_id < 1 or vlan_id > 4094:
            raise ValueError(f"Invalid VLAN ID: {vlan_id}")
        
        # Calculate VLAN table entry
        port_mask = 0
        for port in ports:
            if port < 0 or port > 4:
                raise ValueError(f"Invalid port number: {port}")
            port_mask |= (1 << port)
        
        # VLAN entry format: [VLAN_ID][PORT_MASK][TAGGED]
        entry = (vlan_id << 16) | (port_mask << 8) | (0xFF if tagged else 0x00)
        
        # Write to VLAN lookup table
        table_offset = vlan_id * 4
        self.write_register(SJA1110Registers.VLAN_LOOKUP_TABLE + table_offset, entry)
        
        self.logger.info(f"VLAN {vlan_id} configured: ports={ports}, tagged={tagged}")
    
    def configure_cbs(self, port: int, class_a_bw: int, class_b_bw: int):
        """
        Configure Credit-Based Shaper (CBS) for AVB/TSN
        
        Args:
            port: Port number
            class_a_bw: Class A bandwidth in Mbps
            class_b_bw: Class B bandwidth in Mbps
        """
        if port < 0 or port > 4:
            raise ValueError(f"Invalid port number: {port}")
        
        # Calculate idle slope values
        # Assuming 1Gbps link speed
        link_speed = 1000  # Mbps
        idle_slope_a = int((class_a_bw / link_speed) * 0xFFFF)
        idle_slope_b = int((class_b_bw / link_speed) * 0xFFFF)
        
        # CBS configuration register offset
        cbs_offset = port * 0x10
        
        # Write Class A configuration
        self.write_register(SJA1110Registers.CBS_CONFIG + cbs_offset, idle_slope_a)
        
        # Write Class B configuration
        self.write_register(SJA1110Registers.CBS_CONFIG + cbs_offset + 4, idle_slope_b)
        
        self.logger.info(f"CBS configured for port {port}: "
                        f"Class A={class_a_bw}Mbps, Class B={class_b_bw}Mbps")
    
    def configure_tas(self, port: int, schedule: List[Dict[str, Any]]):
        """
        Configure Time-Aware Shaper (TAS) schedule
        
        Args:
            port: Port number
            schedule: List of gate control entries
        """
        if port < 0 or port > 4:
            raise ValueError(f"Invalid port number: {port}")
        
        # TAS base address for port
        tas_base = SJA1110Registers.TAS_CONFIG + (port * 0x1000)
        
        # Write schedule entries
        for i, entry in enumerate(schedule):
            gate_mask = entry.get('gate_mask', 0xFF)
            time_interval = entry.get('interval_ns', 1000000)  # Default 1ms
            
            # Convert nanoseconds to clock cycles (assuming 125MHz clock)
            clock_cycles = time_interval // 8
            
            # TAS entry format: [GATE_MASK][INTERVAL]
            tas_entry = (gate_mask << 24) | (clock_cycles & 0xFFFFFF)
            
            # Write entry to schedule table
            self.write_register(tas_base + (i * 4), tas_entry)
        
        # Enable TAS for port
        ctrl_reg = tas_base + 0x100
        self.write_register(ctrl_reg, 0x01)  # Enable TAS
        
        self.logger.info(f"TAS configured for port {port}: {len(schedule)} entries")
    
    def enable_ptp(self, port: int = -1):
        """
        Enable Precision Time Protocol (PTP)
        
        Args:
            port: Port number (-1 for all ports)
        """
        if port == -1:
            # Enable PTP on all ports
            ptp_ctrl = 0x1F  # All 5 ports
        else:
            if port < 0 or port > 4:
                raise ValueError(f"Invalid port number: {port}")
            ptp_ctrl = 1 << port
        
        # Enable PTP
        self.write_register(SJA1110Registers.PTP_CONFIG, ptp_ctrl)
        
        # Configure PTP clock
        clock_cfg = 0x01  # Enable PTP clock
        self.write_register(SJA1110Registers.PTP_CONFIG + 0x10, clock_cfg)
        
        self.logger.info(f"PTP enabled on {'all ports' if port == -1 else f'port {port}'}")
    
    def get_statistics(self, port: int) -> Dict[str, int]:
        """
        Get port statistics
        
        Args:
            port: Port number
        
        Returns:
            Dictionary with statistics counters
        """
        if port < 0 or port > 4:
            raise ValueError(f"Invalid port number: {port}")
        
        stats_base = SJA1110Registers.STATS_PORT_0 + (port * 0x10000)
        
        stats = {
            'rx_packets': self.read_register(stats_base + 0x00),
            'tx_packets': self.read_register(stats_base + 0x04),
            'rx_bytes': self.read_register(stats_base + 0x08, 8),
            'tx_bytes': self.read_register(stats_base + 0x10, 8),
            'rx_errors': self.read_register(stats_base + 0x18),
            'tx_errors': self.read_register(stats_base + 0x1C),
            'rx_dropped': self.read_register(stats_base + 0x20),
            'tx_dropped': self.read_register(stats_base + 0x24),
        }
        
        return stats
    
    def close(self):
        """Close communication interface"""
        if self.interface == "spi" and hasattr(self, 'spi'):
            self.spi.close()
        elif self.interface == "i2c" and hasattr(self, 'i2c_bus'):
            self.i2c_bus.close()
        self.logger.info("Driver closed")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize driver with SPI interface
    driver = SJA1110Driver(interface="spi", bus=0, device=0)
    
    # Get port status
    for port in range(5):
        status = driver.get_port_status(port)
        print(f"Port {port}: {status}")
    
    # Configure VLAN
    driver.configure_vlan(vlan_id=100, ports=[0, 1, 2], tagged=True)
    
    # Configure CBS for TSN
    driver.configure_cbs(port=0, class_a_bw=75, class_b_bw=75)
    
    # Enable PTP
    driver.enable_ptp()
    
    driver.close()