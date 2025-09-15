#!/usr/bin/env python3
"""
Gold Box FRER Test Script
Validates frame replication and elimination functionality
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime
from scapy.all import *
import netifaces

class GoldBoxFRERTester:
    def __init__(self):
        self.test_results = []
        self.log_file = f"frer_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(self.log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def get_interface_ip(self, iface):
        """Get IP address of interface"""
        try:
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_INET in addrs:
                return addrs[netifaces.AF_INET][0]['addr']
        except:
            pass
        return None
    
    def send_test_frame(self, iface, dst_mac, vlan_id=None, seq_num=0):
        """Send test frame with sequence number"""
        src_mac = get_if_hwaddr(iface)
        
        # Create Ethernet frame
        eth = Ether(src=src_mac, dst=dst_mac)
        
        # Add VLAN if specified
        if vlan_id:
            dot1q = Dot1Q(vlan=vlan_id, prio=7)
            payload = f"FRER_TEST_SEQ_{seq_num:06d}"
            pkt = eth/dot1q/Raw(load=payload.encode())
        else:
            payload = f"FRER_TEST_SEQ_{seq_num:06d}"
            pkt = eth/Raw(load=payload.encode())
        
        sendp(pkt, iface=iface, verbose=False)
        return seq_num
    
    def capture_frames(self, iface, timeout=5, filter_str=""):
        """Capture frames on interface"""
        packets = []
        
        def packet_handler(pkt):
            packets.append(pkt)
        
        sniff(iface=iface, prn=packet_handler, timeout=timeout, 
              filter=filter_str, store=False)
        
        return packets
    
    def test_replication(self, src_port, dst_ports, vlan_id=100):
        """Test frame replication from src_port to dst_ports"""
        self.log(f"\n=== Testing Replication: {src_port} -> {dst_ports} ===")
        
        # Send test frames
        num_frames = 10
        dst_mac = "ff:ff:ff:ff:ff:ff"  # Broadcast for testing
        
        self.log(f"Sending {num_frames} frames on {src_port}")
        for i in range(num_frames):
            self.send_test_frame(src_port, dst_mac, vlan_id, i)
            time.sleep(0.1)
        
        # Capture on destination ports
        results = {}
        for dst_port in dst_ports:
            self.log(f"Capturing on {dst_port}...")
            packets = self.capture_frames(dst_port, timeout=2)
            
            # Count FRER test frames
            frer_frames = 0
            sequences = []
            for pkt in packets:
                if Raw in pkt:
                    payload = pkt[Raw].load.decode('utf-8', errors='ignore')
                    if 'FRER_TEST_SEQ' in payload:
                        frer_frames += 1
                        # Extract sequence number
                        try:
                            seq = int(payload.split('_')[-1])
                            sequences.append(seq)
                        except:
                            pass
            
            results[dst_port] = {
                'received': frer_frames,
                'sequences': sorted(sequences)
            }
            
            self.log(f"  {dst_port}: Received {frer_frames}/{num_frames} frames")
            if sequences:
                self.log(f"    Sequences: {sequences}")
        
        # Verify replication
        success = all(r['received'] >= num_frames * 0.9 for r in results.values())
        
        test_result = {
            'test': 'replication',
            'src': src_port,
            'dst': dst_ports,
            'success': success,
            'results': results
        }
        self.test_results.append(test_result)
        
        if success:
            self.log("✓ Replication test PASSED")
        else:
            self.log("✗ Replication test FAILED")
        
        return success
    
    def test_elimination(self, src_ports, dst_port, vlan_id=100):
        """Test duplicate elimination"""
        self.log(f"\n=== Testing Elimination: {src_ports} -> {dst_port} ===")
        
        # Send same frame from multiple sources
        num_frames = 10
        dst_mac = get_if_hwaddr(dst_port) if dst_port else "ff:ff:ff:ff:ff:ff"
        
        self.log(f"Sending {num_frames} duplicate frames from {src_ports}")
        for i in range(num_frames):
            # Send same sequence from all source ports
            for src_port in src_ports:
                self.send_test_frame(src_port, dst_mac, vlan_id, i)
            time.sleep(0.1)
        
        # Capture on destination
        self.log(f"Capturing on {dst_port}...")
        packets = self.capture_frames(dst_port, timeout=3)
        
        # Count unique sequences
        sequences = []
        for pkt in packets:
            if Raw in pkt:
                payload = pkt[Raw].load.decode('utf-8', errors='ignore')
                if 'FRER_TEST_SEQ' in payload:
                    try:
                        seq = int(payload.split('_')[-1])
                        sequences.append(seq)
                    except:
                        pass
        
        unique_sequences = set(sequences)
        duplicates = len(sequences) - len(unique_sequences)
        
        self.log(f"  Received {len(sequences)} frames, {len(unique_sequences)} unique")
        self.log(f"  Duplicates eliminated: {duplicates}")
        
        # Success if we got mostly unique frames (allow some duplicates due to timing)
        success = len(unique_sequences) >= num_frames * 0.9 and duplicates < num_frames * 0.2
        
        test_result = {
            'test': 'elimination',
            'src': src_ports,
            'dst': dst_port,
            'success': success,
            'total_frames': len(sequences),
            'unique_frames': len(unique_sequences),
            'duplicates': duplicates
        }
        self.test_results.append(test_result)
        
        if success:
            self.log("✓ Elimination test PASSED")
        else:
            self.log("✗ Elimination test FAILED")
        
        return success
    
    def run_all_tests(self):
        """Run all FRER tests based on configuration"""
        self.log("=" * 60)
        self.log("Gold Box FRER Test Suite")
        self.log("=" * 60)
        
        # Load test plan
        with open('goldbox_frer_testplan.json', 'r') as f:
            test_plan = json.load(f)
        
        all_passed = True
        
        for scenario in test_plan['scenarios']:
            self.log(f"\n### Scenario: {scenario['name']} ###")
            self.log(f"Description: {scenario['description']}")
            
            # Map logical ports to actual interfaces
            # Note: Adjust these mappings based on your actual setup
            port_map = {
                'PFE_MAC0': 'pfe0',
                'P2A': 'enp2s0',  # Adjust to actual interface
                'P2B': 'enp3s0',  # Adjust to actual interface
                'P6': 'sw0p6',
                'P7': 'sw0p7',
                'P8': 'sw0p8',
                'P9': 'sw0p9',
                'P10': 'sw0p10',
                'P11': 'sw0p11'
            }
            
            # Test based on scenario type
            if 'PFE_to_P2AB' in scenario['name']:
                # Test PFE to external replication
                src = port_map.get('PFE_MAC0', 'pfe0')
                dst = [port_map.get('P2A', 'enp2s0'), port_map.get('P2B', 'enp3s0')]
                if not self.test_replication(src, dst):
                    all_passed = False
                    
            elif 'P2A_to_PFE' in scenario['name']:
                # Test external to PFE with elimination
                src = [port_map.get('P6', 'sw0p6'), port_map.get('P7', 'sw0p7')]
                dst = port_map.get('PFE_MAC0', 'pfe0')
                if not self.test_elimination(src, dst):
                    all_passed = False
                    
            elif 'T1_Ring' in scenario['name']:
                # Test T1 ring redundancy
                src = port_map.get('P6', 'sw0p6')
                dst = [port_map.get('P7', 'sw0p7'), port_map.get('P8', 'sw0p8')]
                if not self.test_replication(src, dst):
                    all_passed = False
                    
            elif 'Critical' in scenario['name']:
                # Test triple redundancy
                src = port_map.get('PFE_MAC0', 'pfe0')
                dst = [port_map.get('P6', 'sw0p6'), 
                       port_map.get('P7', 'sw0p7'), 
                       port_map.get('P8', 'sw0p8')]
                if not self.test_replication(src, dst):
                    all_passed = False
        
        # Generate report
        self.generate_report()
        
        return all_passed
    
    def generate_report(self):
        """Generate test report"""
        report_file = f"frer_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'log_file': self.log_file,
            'test_results': self.test_results,
            'summary': {
                'total_tests': len(self.test_results),
                'passed': sum(1 for r in self.test_results if r['success']),
                'failed': sum(1 for r in self.test_results if not r['success'])
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"\n=== Test Summary ===")
        self.log(f"Total tests: {report['summary']['total_tests']}")
        self.log(f"Passed: {report['summary']['passed']}")
        self.log(f"Failed: {report['summary']['failed']}")
        self.log(f"Report saved to: {report_file}")

def main():
    # Check if running as root
    if os.geteuid() != 0:
        print("Error: This script must be run as root (for packet capture)")
        sys.exit(1)
    
    tester = GoldBoxFRERTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()