#!/usr/bin/env python3
"""
SJA1110 Gold Box CLI Control Tool
Command-line interface for NXP Gold Box SJA1110 switch control
"""

import os
import sys
import json
import time
import serial
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sja1110_driver import SJA1110Driver
from sja1110_frer import SJA1110FRER, StreamIdentification, FRERAlgorithm
from sja1110_firmware_builder import SJA1110FirmwareBuilder

class SJA1110CLI:
    """Command-line interface for SJA1110 control"""
    
    def __init__(self, interface: str = 'serial', **kwargs):
        """
        Initialize CLI
        
        Args:
            interface: Communication interface ('serial', 'spi', 'i2c')
            **kwargs: Interface-specific parameters
        """
        self.logger = logging.getLogger(__name__)
        self.interface = interface
        
        if interface == 'serial':
            self.serial_port = kwargs.get('port', '/dev/ttyUSB0')
            self.baudrate = kwargs.get('baudrate', 115200)
            self._init_serial()
        else:
            self.driver = SJA1110Driver(interface=interface, **kwargs)
    
    def _init_serial(self):
        """Initialize serial connection for Gold Box"""
        try:
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=self.baudrate,
                timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            self.logger.info(f"Serial port opened: {self.serial_port} @ {self.baudrate}")
        except Exception as e:
            self.logger.error(f"Failed to open serial port: {e}")
            raise
    
    def send_command(self, command: str) -> str:
        """Send command to Gold Box via serial"""
        if not hasattr(self, 'serial'):
            raise RuntimeError("Serial interface not initialized")
        
        # Send command
        cmd_bytes = (command + '\r\n').encode()
        self.serial.write(cmd_bytes)
        
        # Read response
        response = ''
        timeout = time.time() + 5  # 5 second timeout
        
        while time.time() < timeout:
            if self.serial.in_waiting:
                data = self.serial.read(self.serial.in_waiting)
                response += data.decode('utf-8', errors='ignore')
                
                # Check for prompt or completion
                if '>' in response or '#' in response:
                    break
            time.sleep(0.01)
        
        return response.strip()
    
    def get_version(self) -> str:
        """Get firmware version"""
        if self.interface == 'serial':
            return self.send_command('version')
        else:
            device_id = self.driver.read_register(0x000000)
            return f"Device ID: 0x{device_id:08X}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get switch status"""
        status = {}
        
        if self.interface == 'serial':
            response = self.send_command('status')
            # Parse response
            for line in response.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    status[key.strip()] = value.strip()
        else:
            # Get port status from driver
            status['ports'] = []
            for port in range(5):
                port_status = self.driver.get_port_status(port)
                status['ports'].append(port_status)
        
        return status
    
    def configure_frer(self, config_file: str):
        """Configure FRER from JSON file"""
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        frer = SJA1110FRER()
        
        # Add streams
        for stream_cfg in config.get('streams', []):
            stream = StreamIdentification(
                stream_handle=stream_cfg['handle'],
                source_mac=stream_cfg.get('source_mac'),
                dest_mac=stream_cfg.get('dest_mac'),
                vlan_id=stream_cfg.get('vlan_id'),
                priority=stream_cfg.get('priority')
            )
            frer.add_stream(stream)
        
        # Configure replication
        for rep_cfg in config.get('replication', []):
            frer.configure_replication(
                stream_handle=rep_cfg['stream_handle'],
                egress_ports=rep_cfg['ports']
            )
        
        # Configure elimination
        for elim_cfg in config.get('elimination', []):
            algorithm = FRERAlgorithm[elim_cfg.get('algorithm', 'VECTOR_RECOVERY')]
            frer.configure_elimination(
                stream_handle=elim_cfg['stream_handle'],
                ingress_port=elim_cfg['port'],
                algorithm=algorithm,
                history_length=elim_cfg.get('history_length', 8),
                reset_timeout=elim_cfg.get('reset_timeout', 100)
            )
        
        # Generate and save configuration
        frer.save_configuration('frer_config.bin')
        
        if self.interface == 'serial':
            # Upload configuration via serial
            self._upload_config('frer_config.bin')
        else:
            # Write configuration directly
            config_data = frer.generate_configuration()
            offset = 0x060000  # FRER configuration offset
            
            for i in range(0, len(config_data), 4):
                value = int.from_bytes(config_data[i:i+4], 'big')
                self.driver.write_register(offset + i, value)
        
        self.logger.info("FRER configuration applied")
    
    def _upload_config(self, filename: str):
        """Upload configuration file to Gold Box"""
        with open(filename, 'rb') as f:
            data = f.read()
        
        # Send upload command
        response = self.send_command(f'upload {len(data)}')
        
        if 'ready' not in response.lower():
            raise RuntimeError(f"Upload failed: {response}")
        
        # Send data in chunks
        chunk_size = 256
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            self.serial.write(chunk)
            time.sleep(0.01)  # Small delay between chunks
        
        # Wait for confirmation
        response = self.serial.read(100).decode('utf-8', errors='ignore')
        
        if 'success' in response.lower():
            self.logger.info(f"Configuration uploaded: {filename}")
        else:
            raise RuntimeError(f"Upload failed: {response}")
    
    def flash_firmware(self, firmware_file: str):
        """Flash firmware to Gold Box"""
        if self.interface != 'serial':
            raise RuntimeError("Firmware flashing requires serial interface")
        
        # Validate firmware
        builder = SJA1110FirmwareBuilder()
        if not builder.validate_firmware(firmware_file):
            raise ValueError("Invalid firmware file")
        
        file_size = os.path.getsize(firmware_file)
        
        # Enter bootloader mode
        response = self.send_command('bootloader')
        if 'bootloader' not in response.lower():
            raise RuntimeError("Failed to enter bootloader mode")
        
        time.sleep(1)
        
        # Send flash command
        response = self.send_command(f'flash {file_size}')
        if 'ready' not in response.lower():
            raise RuntimeError(f"Flash preparation failed: {response}")
        
        # Send firmware data
        with open(firmware_file, 'rb') as f:
            chunk_size = 1024
            total_sent = 0
            
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                self.serial.write(chunk)
                total_sent += len(chunk)
                
                # Progress update
                progress = (total_sent / file_size) * 100
                print(f"\rFlashing: {progress:.1f}%", end='')
                
                time.sleep(0.01)
        
        print()  # New line after progress
        
        # Wait for flash completion
        timeout = time.time() + 30  # 30 second timeout
        while time.time() < timeout:
            if self.serial.in_waiting:
                response = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                if 'success' in response.lower():
                    self.logger.info("Firmware flashed successfully")
                    
                    # Reboot
                    self.send_command('reboot')
                    return
                elif 'error' in response.lower():
                    raise RuntimeError(f"Flash failed: {response}")
            time.sleep(0.1)
        
        raise RuntimeError("Flash timeout")
    
    def reset(self):
        """Reset the switch"""
        if self.interface == 'serial':
            response = self.send_command('reset')
            self.logger.info(f"Reset response: {response}")
        else:
            self.driver.reset()
    
    def close(self):
        """Close connection"""
        if hasattr(self, 'serial'):
            self.serial.close()
        elif hasattr(self, 'driver'):
            self.driver.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='SJA1110 Gold Box Control Tool')
    
    # Connection options
    parser.add_argument('-i', '--interface', 
                       choices=['serial', 'spi', 'i2c'],
                       default='serial',
                       help='Communication interface')
    parser.add_argument('-p', '--port', 
                       default='/dev/ttyUSB0',
                       help='Serial port (for serial interface)')
    parser.add_argument('-b', '--baudrate',
                       type=int,
                       default=115200,
                       help='Serial baudrate')
    
    # Commands
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Version command
    subparsers.add_parser('version', help='Get firmware version')
    
    # Status command
    subparsers.add_parser('status', help='Get switch status')
    
    # FRER configuration
    frer_parser = subparsers.add_parser('frer', help='Configure FRER')
    frer_parser.add_argument('config', help='FRER configuration JSON file')
    
    # Firmware flash
    flash_parser = subparsers.add_parser('flash', help='Flash firmware')
    flash_parser.add_argument('firmware', help='Firmware binary file')
    
    # Reset command
    subparsers.add_parser('reset', help='Reset switch')
    
    # Build firmware
    build_parser = subparsers.add_parser('build', help='Build firmware')
    build_parser.add_argument('-c', '--config', help='Configuration JSON file')
    build_parser.add_argument('-o', '--output', 
                             default='sja1110_firmware.bin',
                             help='Output firmware file')
    
    # Interactive mode
    subparsers.add_parser('interactive', help='Enter interactive mode')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Execute command
    if args.command == 'build':
        # Build firmware
        from sja1110_firmware_builder import create_example_firmware
        firmware_file = create_example_firmware()
        print(f"Firmware built: {firmware_file}")
        
    elif args.command:
        # Initialize CLI
        cli = SJA1110CLI(
            interface=args.interface,
            port=args.port,
            baudrate=args.baudrate
        )
        
        try:
            if args.command == 'version':
                version = cli.get_version()
                print(f"Version: {version}")
                
            elif args.command == 'status':
                status = cli.get_status()
                print("Switch Status:")
                print(json.dumps(status, indent=2))
                
            elif args.command == 'frer':
                cli.configure_frer(args.config)
                print("FRER configuration applied")
                
            elif args.command == 'flash':
                cli.flash_firmware(args.firmware)
                print("Firmware flashed successfully")
                
            elif args.command == 'reset':
                cli.reset()
                print("Switch reset")
                
            elif args.command == 'interactive':
                print("SJA1110 Interactive Mode")
                print("Type 'help' for commands, 'exit' to quit")
                
                while True:
                    try:
                        cmd = input("> ").strip()
                        
                        if cmd == 'exit':
                            break
                        elif cmd == 'help':
                            print("Commands:")
                            print("  version  - Get firmware version")
                            print("  status   - Get switch status")
                            print("  reset    - Reset switch")
                            print("  exit     - Exit interactive mode")
                        elif cmd == 'version':
                            print(cli.get_version())
                        elif cmd == 'status':
                            status = cli.get_status()
                            print(json.dumps(status, indent=2))
                        elif cmd == 'reset':
                            cli.reset()
                            print("Switch reset")
                        elif cmd:
                            # Send raw command
                            response = cli.send_command(cmd)
                            print(response)
                            
                    except KeyboardInterrupt:
                        print("\nUse 'exit' to quit")
                    except Exception as e:
                        print(f"Error: {e}")
                
        finally:
            cli.close()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()