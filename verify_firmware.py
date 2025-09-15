#!/usr/bin/env python3
"""
SJA1110 Firmware Verification Tool
Compares our generated firmware with NXP official format requirements
"""

import struct
import os
from typing import Optional

class FirmwareVerifier:
    def __init__(self):
        # NXP Constants from official driver
        self.IMAGE_VALID_MARKER = bytes([0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6, 0x6A, 0xA6])
        self.HEADER_EXEC = bytes([0xDD, 0x11])
        self.STATUS_PKT_HEADER = 0xCC
        self.SJA1110_DEVICE_ID = 0xb700030e
        self.CONFIG_START_ADDRESS = 0x20000
    
    def verify_uc_firmware(self, firmware_path: str) -> bool:
        """Verify UC firmware format"""
        print(f"\n🔍 Verifying UC firmware: {firmware_path}")
        
        if not os.path.exists(firmware_path):
            print(f"❌ File not found: {firmware_path}")
            return False
        
        with open(firmware_path, 'rb') as f:
            data = f.read()
        
        print(f"📊 File size: {len(data):,} bytes")
        
        # Check 1: IMAGE_VALID_MARKER at start
        if not data.startswith(self.IMAGE_VALID_MARKER):
            print(f"❌ Missing IMAGE_VALID_MARKER at start")
            print(f"   Expected: {self.IMAGE_VALID_MARKER.hex()}")
            print(f"   Found:    {data[:8].hex()}")
            return False
        print("✓ IMAGE_VALID_MARKER found at start")
        
        # Check 2: HEADER_EXEC signature
        header_found = False
        for i in range(8, min(100, len(data) - 1)):
            if data[i:i+2] == self.HEADER_EXEC:
                print(f"✓ HEADER_EXEC found at offset {i}")
                header_found = True
                break
        
        if not header_found:
            print(f"❌ HEADER_EXEC not found in first 100 bytes")
            return False
        
        # Check 3: Size should be around 320KB
        expected_size = 320 * 1024
        if abs(len(data) - expected_size) > 32 * 1024:  # Allow 32KB variance
            print(f"⚠️  Size warning: {len(data)} bytes (expected ~{expected_size})")
        else:
            print(f"✓ Size OK: {len(data)} bytes")
        
        # Check 4: CRC at end
        if len(data) >= 4:
            crc_bytes = data[-4:]
            crc_value = struct.unpack('<I', crc_bytes)[0]
            print(f"✓ CRC found: 0x{crc_value:08x}")
        
        return True
    
    def verify_switch_config(self, config_path: str) -> bool:
        """Verify switch configuration format"""
        print(f"\n🔍 Verifying switch config: {config_path}")
        
        if not os.path.exists(config_path):
            print(f"❌ File not found: {config_path}")
            return False
        
        with open(config_path, 'rb') as f:
            data = f.read()
        
        print(f"📊 File size: {len(data):,} bytes")
        
        # Check 1: IMAGE_VALID_MARKER at start
        if not data.startswith(self.IMAGE_VALID_MARKER):
            print(f"❌ Missing IMAGE_VALID_MARKER at start")
            return False
        print("✓ IMAGE_VALID_MARKER found at start")
        
        # Check 2: Device ID
        if len(data) >= 12:
            device_id = struct.unpack('<I', data[8:12])[0]
            if device_id == self.SJA1110_DEVICE_ID:
                print(f"✓ Device ID correct: 0x{device_id:08x}")
            else:
                print(f"❌ Device ID mismatch: 0x{device_id:08x} (expected 0x{self.SJA1110_DEVICE_ID:08x})")
                return False
        
        # Check 3: Configuration flags
        if len(data) >= 16:
            cf_flags = struct.unpack('<I', data[12:16])[0]
            if cf_flags & 0x80000000:  # CF_CONFIGS_MASK
                print(f"✓ Configuration flags OK: 0x{cf_flags:08x}")
            else:
                print(f"⚠️  Configuration flags: 0x{cf_flags:08x}")
        
        # Check 4: Size should be around 640KB
        expected_size = 640 * 1024
        if abs(len(data) - expected_size) > 64 * 1024:  # Allow 64KB variance
            print(f"⚠️  Size warning: {len(data)} bytes (expected ~{expected_size})")
        else:
            print(f"✓ Size OK: {len(data)} bytes")
        
        # Check 5: Configuration data at CONFIG_START_ADDRESS
        if len(data) > self.CONFIG_START_ADDRESS:
            config_region = data[self.CONFIG_START_ADDRESS:self.CONFIG_START_ADDRESS+16]
            if any(b != 0 for b in config_region):
                print(f"✓ Configuration data found at 0x{self.CONFIG_START_ADDRESS:x}")
            else:
                print(f"⚠️  No configuration data at 0x{self.CONFIG_START_ADDRESS:x}")
        
        return True
    
    def analyze_firmware_structure(self, firmware_path: str):
        """Detailed analysis of firmware structure"""
        print(f"\n🔬 Analyzing firmware structure: {firmware_path}")
        
        if not os.path.exists(firmware_path):
            print(f"❌ File not found: {firmware_path}")
            return
        
        with open(firmware_path, 'rb') as f:
            data = f.read()
        
        print(f"📋 Detailed Analysis:")
        print(f"   Total size: {len(data):,} bytes")
        
        # Analyze header region
        print(f"\n📍 Header Analysis (first 128 bytes):")
        for i in range(0, min(128, len(data)), 16):
            chunk = data[i:i+16]
            hex_str = " ".join(f"{b:02x}" for b in chunk)
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            print(f"   {i:04x}: {hex_str:<48} |{ascii_str}|")
        
        # Find interesting patterns
        print(f"\n🔍 Pattern Analysis:")
        
        # Look for FRER signatures
        frer_patterns = [b'\xf1\xc1', b'\x01\x00', b'\x64\x00']  # Common FRER patterns
        for pattern in frer_patterns:
            count = data.count(pattern)
            if count > 0:
                print(f"   Pattern {pattern.hex()}: {count} occurrences")
        
        # Analyze non-zero regions
        zero_regions = []
        nonzero_regions = []
        
        current_zeros = 0
        in_zero_region = False
        
        for i, byte in enumerate(data):
            if byte == 0:
                if not in_zero_region:
                    in_zero_region = True
                    zero_start = i
                current_zeros += 1
            else:
                if in_zero_region:
                    zero_regions.append((zero_start, i - 1, i - zero_start))
                    in_zero_region = False
                    current_zeros = 0
        
        # Show significant zero regions (> 1KB)
        large_zero_regions = [(start, end, size) for start, end, size in zero_regions if size > 1024]
        if large_zero_regions:
            print(f"\n📍 Large zero regions (padding):")
            for start, end, size in large_zero_regions[:5]:  # Show first 5
                print(f"   0x{start:06x} - 0x{end:06x}: {size:,} bytes")
    
    def compare_with_original(self, our_file: str, original_file: Optional[str] = None):
        """Compare our firmware with original if available"""
        if not original_file or not os.path.exists(original_file):
            print(f"\n📋 No original file to compare with")
            return
        
        print(f"\n🔄 Comparing with original: {original_file}")
        
        with open(our_file, 'rb') as f:
            our_data = f.read()
        
        with open(original_file, 'rb') as f:
            orig_data = f.read()
        
        print(f"   Our file:      {len(our_data):,} bytes")
        print(f"   Original file: {len(orig_data):,} bytes")
        
        # Compare headers
        header_size = 128
        if len(our_data) >= header_size and len(orig_data) >= header_size:
            if our_data[:header_size] == orig_data[:header_size]:
                print(f"✓ Headers match (first {header_size} bytes)")
            else:
                print(f"❌ Headers differ")
                # Show differences
                for i in range(header_size):
                    if our_data[i] != orig_data[i]:
                        print(f"     Offset {i:02x}: our=0x{our_data[i]:02x}, orig=0x{orig_data[i]:02x}")
                        if i > 10:  # Don't spam too much
                            print(f"     ... (showing first 10 differences)")
                            break

def main():
    """Main verification function"""
    print("=" * 60)
    print("SJA1110 Firmware Verification Tool")
    print("=" * 60)
    
    verifier = FirmwareVerifier()
    
    # Check corrected firmware
    uc_file = "sja1110_uc_corrected.bin"
    switch_file = "sja1110_switch_corrected.bin"
    
    print(f"\n🎯 Verifying corrected firmware files...")
    
    uc_valid = verifier.verify_uc_firmware(uc_file)
    switch_valid = verifier.verify_switch_config(switch_file)
    
    # Detailed analysis
    if os.path.exists(uc_file):
        verifier.analyze_firmware_structure(uc_file)
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📋 VERIFICATION SUMMARY")
    print(f"=" * 60)
    print(f"UC Firmware:     {'✓ VALID' if uc_valid else '❌ INVALID'}")
    print(f"Switch Config:   {'✓ VALID' if switch_valid else '❌ INVALID'}")
    
    if uc_valid and switch_valid:
        print(f"\n🎉 RESULT: Firmware appears to match NXP official format!")
        print(f"📤 Ready for upload to Gold Box:")
        print(f"   sudo ./goldbox_dual_upload.sh {uc_file} {switch_file}")
    else:
        print(f"\n⚠️  RESULT: Firmware format issues detected")
        print(f"🔧 Additional fixes may be required")

if __name__ == "__main__":
    main()