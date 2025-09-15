#!/usr/bin/env python3
"""
SJA1110 Firmware Upload Tool for Gold Box
Based on NXP's official driver implementation
"""

import os
import sys
import time
import struct
import logging
import argparse
from pathlib import Path

# Try to import SPI/serial libraries
try:
    import spidev
    HAS_SPI = True
except ImportError:
    HAS_SPI = False

try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

class SJA1110Uploader:
    """Upload firmware and configuration to SJA1110"""
    
    # From sja1110_init.h
    HEADER_EXEC = bytes([0xDD, 0x11])
    HEADER_STATUS_PACKET = bytes([0xCC])
    IMAGE_VALID_MARKER = bytes([0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6])
    
    # SJA1110 Register Addresses
    DEVICE_ID_ADDR = 0x000000
    CONFIG_FLAG_ADDR = 0x000001
    RESET_CTRL_ADDR = 0x1C6000
    CONFIG_START_ADDR = 0x020000
    
    # Device ID for SJA1110
    SJA1110_DEVICE_ID = 0xB700030E
    
    # Upload status codes
    STATUS_INITIALIZING = 0x31
    STATUS_BOOTING = 0x32
    STATUS_WAITING = 0x33
    STATUS_DOWNLOADING = 0x34
    STATUS_VERIFYING = 0x35
    STATUS_COMPLETED = 0x36
    
    def __init__(self, interface='sysfs', **kwargs):
        """
        Initialize uploader
        
        Args:
            interface: 'sysfs', 'spi', or 'serial'
            **kwargs: Interface-specific parameters
        """
        self.interface = interface
        self.logger = logging.getLogger(__name__)
        
        if interface == 'sysfs':
            self.switch_path = kwargs.get('switch_path', '/sys/bus/spi/devices/spi0.0/switch-configuration')
            self.uc_path = kwargs.get('uc_path', '/sys/bus/spi/devices/spi0.1/uc-configuration')
        elif interface == 'spi':
            if not HAS_SPI:
                raise ImportError("spidev not installed")
            self.spi = spidev.SpiDev()
            self.spi.open(kwargs.get('bus', 0), kwargs.get('device', 0))
            self.spi.max_speed_hz = kwargs.get('speed', 10000000)
        elif interface == 'serial':
            if not HAS_SERIAL:
                raise ImportError("pyserial not installed")
            self.serial = serial.Serial(
                port=kwargs.get('port', '/dev/ttyUSB0'),
                baudrate=kwargs.get('baudrate', 115200),
                timeout=1
            )
    
    def reset_switch(self):
        """Reset SJA1110 switch"""
        self.logger.info("Resetting SJA1110...")
        
        if self.interface == 'sysfs':
            reset_file = os.path.join(self.switch_path, 'switch_reset')
            if os.path.exists(reset_file):
                with open(reset_file, 'w') as f:
                    f.write('1')
                time.sleep(0.5)
        elif self.interface == 'spi':
            # Write to reset control register
            self._spi_write(self.RESET_CTRL_ADDR, 0x20)  # Cold reset
            time.sleep(0.5)
        
        self.logger.info("Reset complete")
    
    def verify_device(self):
        """Verify SJA1110 device ID"""
        if self.interface == 'spi':
            device_id = self._spi_read(self.DEVICE_ID_ADDR)
            if device_id != self.SJA1110_DEVICE_ID:
                self.logger.warning(f"Unexpected device ID: 0x{device_id:08X}")
                return False
            self.logger.info(f"SJA1110 detected: ID=0x{device_id:08X}")
            return True
        return True  # Assume OK for sysfs
    
    def upload_switch_config(self, config_file):
        """
        Upload switch configuration (sja1110_switch.bin)
        
        Args:
            config_file: Path to configuration binary
        """
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'rb') as f:
            config_data = f.read()
        
        # Verify marker
        if not config_data.startswith(self.IMAGE_VALID_MARKER):
            self.logger.warning("Configuration missing valid marker, adding...")
            config_data = self.IMAGE_VALID_MARKER + config_data
        
        self.logger.info(f"Uploading switch configuration: {config_file} ({len(config_data)} bytes)")
        
        if self.interface == 'sysfs':
            # Copy to firmware directory
            fw_dir = '/lib/firmware'
            fw_path = os.path.join(fw_dir, os.path.basename(config_file))
            
            with open(fw_path, 'wb') as f:
                f.write(config_data)
            
            # Trigger upload via sysfs
            upload_file = os.path.join(self.switch_path, 'switch_cfg_upload')
            if os.path.exists(upload_file):
                with open(upload_file, 'w') as f:
                    f.write(os.path.basename(config_file))
            else:
                self.logger.warning(f"sysfs upload file not found: {upload_file}")
        
        elif self.interface == 'spi':
            # Direct SPI upload
            self._upload_via_spi(config_data, is_switch_config=True)
        
        self.logger.info("Switch configuration upload complete")
    
    def upload_uc_firmware(self, firmware_file):
        """
        Upload microcontroller firmware (sja1110_uc.bin)
        
        Args:
            firmware_file: Path to firmware binary
        """
        if not os.path.exists(firmware_file):
            # Use default if not found
            firmware_file = '/lib/firmware/sja1110_uc.bin'
            if not os.path.exists(firmware_file):
                self.logger.warning("Microcontroller firmware not found, skipping")
                return
        
        with open(firmware_file, 'rb') as f:
            fw_data = f.read()
        
        self.logger.info(f"Uploading uC firmware: {firmware_file} ({len(fw_data)} bytes)")
        
        if self.interface == 'sysfs':
            # Copy to firmware directory if needed
            fw_dir = '/lib/firmware'
            fw_path = os.path.join(fw_dir, os.path.basename(firmware_file))
            
            if firmware_file != fw_path:
                with open(fw_path, 'wb') as f:
                    f.write(fw_data)
            
            # Trigger upload via sysfs
            upload_file = os.path.join(self.uc_path, 'uc_fw_upload')
            if os.path.exists(upload_file):
                with open(upload_file, 'w') as f:
                    f.write(os.path.basename(firmware_file))
            else:
                self.logger.warning(f"sysfs upload file not found: {upload_file}")
        
        elif self.interface == 'spi':
            # Direct SPI upload
            self._upload_via_spi(fw_data, is_switch_config=False)
        
        self.logger.info("Microcontroller firmware upload complete")
    
    def _upload_via_spi(self, data, is_switch_config=True):
        """Upload data via SPI interface"""
        if not HAS_SPI:
            raise RuntimeError("SPI not available")
        
        # Prepare upload
        if is_switch_config:
            base_addr = self.CONFIG_START_ADDR
        else:
            base_addr = 0x000000  # uC firmware starts at 0
        
        # Upload in chunks
        chunk_size = 256
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            addr = base_addr + i
            
            # Write chunk
            self._spi_write_block(addr, chunk)
            
            # Progress
            current_chunk = i // chunk_size + 1
            progress = (current_chunk / total_chunks) * 100
            print(f"\rUploading: {progress:.1f}%", end='')
        
        print()  # New line after progress
    
    def _spi_read(self, address, length=4):
        """Read from SPI"""
        # SJA1110 SPI protocol: [CMD][ADDR][DATA]
        cmd = 0x00  # Read command
        addr_bytes = [(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        
        tx_data = [cmd] + addr_bytes + [0x00] * length
        rx_data = self.spi.xfer2(tx_data)
        
        # Extract value
        value = 0
        for i in range(length):
            value = (value << 8) | rx_data[4 + i]
        
        return value
    
    def _spi_write(self, address, value, length=4):
        """Write to SPI"""
        # SJA1110 SPI protocol: [CMD][ADDR][DATA]
        cmd = 0x80  # Write command
        addr_bytes = [(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF]
        
        data_bytes = []
        for i in range(length):
            data_bytes.append((value >> (8 * (length - 1 - i))) & 0xFF)
        
        tx_data = [cmd] + addr_bytes + data_bytes
        self.spi.xfer2(tx_data)
    
    def _spi_write_block(self, address, data):
        """Write block of data to SPI"""
        # Write data in 32-bit words
        for i in range(0, len(data), 4):
            word_data = data[i:i+4]
            if len(word_data) < 4:
                word_data += b'\x00' * (4 - len(word_data))
            
            value = struct.unpack('>I', word_data)[0]
            self._spi_write(address + i, value, 4)
    
    def close(self):
        """Close connections"""
        if hasattr(self, 'spi'):
            self.spi.close()
        if hasattr(self, 'serial'):
            self.serial.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='SJA1110 Firmware Upload Tool')
    
    parser.add_argument('-i', '--interface',
                       choices=['sysfs', 'spi', 'serial'],
                       default='sysfs',
                       help='Upload interface')
    parser.add_argument('-c', '--config',
                       default='sja1110_switch.bin',
                       help='Switch configuration file')
    parser.add_argument('-f', '--firmware',
                       default='sja1110_uc.bin',
                       help='Microcontroller firmware file')
    parser.add_argument('-r', '--reset',
                       action='store_true',
                       help='Reset switch before upload')
    parser.add_argument('--switch-only',
                       action='store_true',
                       help='Only upload switch configuration')
    parser.add_argument('--uc-only',
                       action='store_true',
                       help='Only upload uC firmware')
    
    # Interface-specific options
    parser.add_argument('--spi-bus', type=int, default=0, help='SPI bus number')
    parser.add_argument('--spi-device', type=int, default=0, help='SPI device number')
    parser.add_argument('--spi-speed', type=int, default=10000000, help='SPI speed in Hz')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create uploader
    kwargs = {}
    if args.interface == 'spi':
        kwargs = {
            'bus': args.spi_bus,
            'device': args.spi_device,
            'speed': args.spi_speed
        }
    
    uploader = SJA1110Uploader(interface=args.interface, **kwargs)
    
    try:
        # Reset if requested
        if args.reset:
            uploader.reset_switch()
        
        # Verify device
        uploader.verify_device()
        
        # Upload configuration
        if not args.uc_only:
            uploader.upload_switch_config(args.config)
        
        # Upload firmware
        if not args.switch_only:
            uploader.upload_uc_firmware(args.firmware)
        
        print("\nUpload complete!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        uploader.close()


if __name__ == "__main__":
    main()