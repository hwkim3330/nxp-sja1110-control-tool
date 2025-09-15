#!/usr/bin/env python3
"""
SJA1110 Gold Box RJ45 FRER Scenarios
Various configurations for RJ45 Ethernet port input replication
"""

import struct
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
from sja1110_dual_firmware import SJA1110FirmwareBuilder

class GoldBoxRJ45Scenarios:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Gold Box Port Mapping (확실한 포트 정보)
        self.port_info = {
            # RJ45 Ports (External)
            1: {'type': '100BASE-TX', 'connector': 'P1 (RJ45)', 'desc': '100Mbps Ethernet'},
            2: {'type': '1000BASE-T', 'connector': 'P2A (RJ45)', 'desc': '1Gbps Ethernet A'},
            3: {'type': '1000BASE-T', 'connector': 'P2B (RJ45)', 'desc': '1Gbps Ethernet B'},
            4: {'type': '1000BASE-T', 'connector': 'P3 (RJ45)', 'desc': '1Gbps Ethernet'},
            
            # 100BASE-T1 Automotive Ports
            5: {'type': '100BASE-T1', 'connector': 'P6 (T1)', 'desc': 'Automotive T1'},
            6: {'type': '100BASE-T1', 'connector': 'P7 (T1)', 'desc': 'Automotive T1'},
            7: {'type': '100BASE-T1', 'connector': 'P8 (T1)', 'desc': 'Automotive T1'},
            8: {'type': '100BASE-T1', 'connector': 'P9 (T1)', 'desc': 'Automotive T1'},
            9: {'type': '100BASE-T1', 'connector': 'P10 (T1)', 'desc': 'Automotive T1'},
            10: {'type': '100BASE-T1', 'connector': 'P11 (T1)', 'desc': 'Automotive T1'},
            
            # Internal CPU Connection
            0: {'type': 'CPU', 'connector': 'S32G PFE', 'desc': 'Host CPU Interface'}
        }
        
    def scenario_basic_rj45_replication(self) -> SJA1110FirmwareBuilder:
        """시나리오 1: 기본 RJ45 입력 복제"""
        builder = SJA1110FirmwareBuilder()
        
        # P1 (100M RJ45) → P2A, P2B (1G RJ45) 복제
        builder.add_frer_replication_stream(
            stream_id=1,
            src_port=1,  # P1 (100BASE-TX)
            dst_ports=[2, 3],  # P2A, P2B (1000BASE-T)
            vlan_id=100,
            priority=7,
            name="P1_to_P2AB_Basic"
        )
        
        # P2A (1G RJ45) → P1, P3 복제 (역방향)
        builder.add_frer_replication_stream(
            stream_id=2,
            src_port=2,  # P2A
            dst_ports=[1, 4],  # P1, P3
            vlan_id=101,
            priority=6,
            name="P2A_to_P1P3_Reverse"
        )
        
        return builder
    
    def scenario_rj45_to_automotive(self) -> SJA1110FirmwareBuilder:
        """시나리오 2: RJ45 → Automotive T1 복제"""
        builder = SJA1110FirmwareBuilder()
        
        # P2A (1G RJ45) → 모든 T1 포트로 브로드캐스트
        builder.add_frer_replication_stream(
            stream_id=1,
            src_port=2,  # P2A (1000BASE-T)
            dst_ports=[5, 6, 7, 8],  # P6-P9 (100BASE-T1)
            vlan_id=200,
            priority=7,
            name="RJ45_to_T1_Broadcast"
        )
        
        # P1 (100M RJ45) → T1 페어 복제
        builder.add_frer_replication_stream(
            stream_id=2,
            src_port=1,  # P1 (100BASE-TX)
            dst_ports=[5, 6],  # P6, P7 (T1)
            vlan_id=201,
            priority=6,
            name="P1_to_T1_Pair"
        )
        
        # P3 (1G RJ45) → 고속 T1 복제
        builder.add_frer_replication_stream(
            stream_id=3,
            src_port=4,  # P3 (1000BASE-T)
            dst_ports=[7, 8, 9],  # P8, P9, P10 (T1)
            vlan_id=202,
            priority=5,
            name="P3_to_T1_High_Speed"
        )
        
        return builder
    
    def scenario_redundant_gateway(self) -> SJA1110FirmwareBuilder:
        """시나리오 3: 이중화 게이트웨이"""
        builder = SJA1110FirmwareBuilder()
        
        # 외부 네트워크 → PFE + T1 백업
        builder.add_frer_replication_stream(
            stream_id=1,
            src_port=2,  # P2A (External Network)
            dst_ports=[0, 5],  # PFE + P6 (T1 backup)
            vlan_id=300,
            priority=7,
            name="External_to_PFE_T1_Backup"
        )
        
        # PFE → 이중 RJ45 출력
        builder.add_frer_replication_stream(
            stream_id=2,
            src_port=0,  # PFE
            dst_ports=[2, 3],  # P2A, P2B (Dual RJ45)
            vlan_id=301,
            priority=7,
            name="PFE_to_Dual_RJ45"
        )
        
        # 크리티컬 제어 → 모든 포트 복제
        builder.add_frer_replication_stream(
            stream_id=3,
            src_port=1,  # P1 (Control input)
            dst_ports=[2, 3, 4, 5, 6],  # 모든 주요 포트
            vlan_id=302,
            priority=7,
            name="Critical_Control_All_Ports"
        )
        
        return builder
    
    def scenario_ring_topology(self) -> SJA1110FirmwareBuilder:
        """시나리오 4: 링 토폴로지 이중화"""
        builder = SJA1110FirmwareBuilder()
        
        # 링 입력 → 양방향 복제
        builder.add_frer_replication_stream(
            stream_id=1,
            src_port=2,  # P2A (Ring input)
            dst_ports=[3, 5],  # P2B (Ring out), P6 (T1 branch)
            vlan_id=400,
            priority=6,
            name="Ring_Input_Bidirectional"
        )
        
        # T1 링 구성
        builder.add_frer_replication_stream(
            stream_id=2,
            src_port=5,  # P6 (T1 input)
            dst_ports=[6, 7],  # P7, P8 (T1 ring)
            vlan_id=401,
            priority=5,
            name="T1_Ring_Forward"
        )
        
        # 백업 경로
        builder.add_frer_replication_stream(
            stream_id=3,
            src_port=7,  # P8 (T1 backup)
            dst_ports=[1, 4],  # P1, P3 (RJ45 backup)
            vlan_id=402,
            priority=4,
            name="T1_to_RJ45_Backup"
        )
        
        return builder
    
    def scenario_load_balancing(self) -> SJA1110FirmwareBuilder:
        """시나리오 5: 로드 밸런싱 복제"""
        builder = SJA1110FirmwareBuilder()
        
        # 고속 입력 분산
        builder.add_frer_replication_stream(
            stream_id=1,
            src_port=2,  # P2A (1G input)
            dst_ports=[1, 4, 5, 6],  # 다중 포트 분산
            vlan_id=500,
            priority=6,
            name="High_Speed_Load_Balance"
        )
        
        # 프리미엄 트래픽 복제
        builder.add_frer_replication_stream(
            stream_id=2,
            src_port=3,  # P2B (Premium input)
            dst_ports=[0, 2, 7, 8],  # PFE + RJ45 + T1
            vlan_id=501,
            priority=7,
            name="Premium_Traffic_Replication"
        )
        
        return builder
    
    def scenario_mixed_automotive(self) -> SJA1110FirmwareBuilder:
        """시나리오 6: 자동차 혼합 네트워크"""
        builder = SJA1110FirmwareBuilder()
        
        # ECU 통신 복제
        builder.add_frer_replication_stream(
            stream_id=1,
            src_port=1,  # P1 (Diagnostic port)
            dst_ports=[5, 6, 7],  # T1 ECU network
            vlan_id=600,
            priority=7,
            name="Diagnostic_to_ECU_Network"
        )
        
        # 센서 데이터 집계
        builder.add_frer_replication_stream(
            stream_id=2,
            src_port=5,  # P6 (T1 sensors)
            dst_ports=[0, 2],  # PFE + External
            vlan_id=601,
            priority=6,
            name="Sensor_Data_Aggregation"
        )
        
        # 안전 메시지 브로드캐스트
        builder.add_frer_replication_stream(
            stream_id=3,
            src_port=0,  # PFE (Safety controller)
            dst_ports=[1, 2, 3, 4, 8, 9, 10],  # 모든 외부 포트
            vlan_id=602,
            priority=7,
            name="Safety_Message_Broadcast"
        )
        
        return builder
    
    def build_all_scenarios(self):
        """모든 시나리오 빌드"""
        scenarios = {
            'basic_rj45': self.scenario_basic_rj45_replication(),
            'rj45_to_automotive': self.scenario_rj45_to_automotive(),
            'redundant_gateway': self.scenario_redundant_gateway(),
            'ring_topology': self.scenario_ring_topology(),
            'load_balancing': self.scenario_load_balancing(),
            'mixed_automotive': self.scenario_mixed_automotive()
        }
        
        print("=" * 60)
        print("Gold Box RJ45 FRER Scenarios Builder")
        print("=" * 60)
        
        for name, builder in scenarios.items():
            print(f"\n=== {name.upper().replace('_', ' ')} ===")
            
            # Build firmware
            uc_firmware = builder.build_microcontroller_firmware()
            switch_config = builder.build_switch_firmware()
            
            # Save files
            uc_file = f"sja1110_uc_{name}.bin"
            switch_file = f"sja1110_switch_{name}.bin"
            
            with open(uc_file, 'wb') as f:
                f.write(uc_firmware)
            with open(switch_file, 'wb') as f:
                f.write(switch_config)
            
            print(f"✓ Created {uc_file} ({len(uc_firmware):,} bytes)")
            print(f"✓ Created {switch_file} ({len(switch_config):,} bytes)")
            
            # Show streams
            print(f"FRER Streams:")
            for stream in builder.frer_streams:
                src_info = self.port_info[stream['src_port']]
                dst_info = [self.port_info[p] for p in stream['dst_ports']]
                dst_names = [info['connector'] for info in dst_info]
                print(f"  • {stream['name']}")
                print(f"    {src_info['connector']} → {dst_names}")
                print(f"    VLAN: {stream['vlan_id']}, Priority: {stream['priority']}")
            
            # Save config
            builder.save_configuration_info(uc_file, switch_file)
        
        # Create scenario comparison
        self.create_scenario_comparison(scenarios)
        
        return scenarios
    
    def create_scenario_comparison(self, scenarios: Dict[str, SJA1110FirmwareBuilder]):
        """시나리오 비교 표 생성"""
        comparison = {
            'scenarios': {},
            'port_usage': {},
            'recommendations': {}
        }
        
        # 각 시나리오 분석
        for name, builder in scenarios.items():
            scenario_info = {
                'stream_count': len(builder.frer_streams),
                'use_case': self.get_use_case_description(name),
                'complexity': self.calculate_complexity(builder),
                'port_mapping': []
            }
            
            for stream in builder.frer_streams:
                src_port = self.port_info[stream['src_port']]
                dst_ports = [self.port_info[p] for p in stream['dst_ports']]
                scenario_info['port_mapping'].append({
                    'src': src_port['connector'],
                    'dst': [p['connector'] for p in dst_ports],
                    'description': stream['name']
                })
            
            comparison['scenarios'][name] = scenario_info
        
        # 포트 사용률 분석
        for port_id, info in self.port_info.items():
            usage_count = 0
            used_in = []
            
            for name, builder in scenarios.items():
                for stream in builder.frer_streams:
                    if port_id == stream['src_port'] or port_id in stream['dst_ports']:
                        usage_count += 1
                        used_in.append(name)
                        break
            
            comparison['port_usage'][info['connector']] = {
                'used_in_scenarios': usage_count,
                'scenarios': used_in,
                'type': info['type']
            }
        
        # 추천사항
        comparison['recommendations'] = {
            'basic_networking': 'basic_rj45',
            'automotive_gateway': 'rj45_to_automotive',
            'high_reliability': 'redundant_gateway',
            'ring_networks': 'ring_topology',
            'high_performance': 'load_balancing',
            'automotive_ecu': 'mixed_automotive'
        }
        
        # JSON 저장
        with open('rj45_scenarios_comparison.json', 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print(f"\n{'='*60}")
        print("Scenario Comparison saved to: rj45_scenarios_comparison.json")
    
    def get_use_case_description(self, scenario_name: str) -> str:
        descriptions = {
            'basic_rj45': 'Basic Ethernet port replication for simple networks',
            'rj45_to_automotive': 'Bridge between RJ45 Ethernet and automotive T1 networks',
            'redundant_gateway': 'High-availability gateway with backup paths',
            'ring_topology': 'Ring network topology with redundant paths',
            'load_balancing': 'Load distribution across multiple ports',
            'mixed_automotive': 'Automotive ECU network with mixed protocols'
        }
        return descriptions.get(scenario_name, 'Custom scenario')
    
    def calculate_complexity(self, builder: SJA1110FirmwareBuilder) -> str:
        stream_count = len(builder.frer_streams)
        total_replications = sum(len(s['dst_ports']) for s in builder.frer_streams)
        
        if stream_count <= 2 and total_replications <= 6:
            return 'Low'
        elif stream_count <= 4 and total_replications <= 12:
            return 'Medium'
        else:
            return 'High'

def main():
    scenarios = GoldBoxRJ45Scenarios()
    scenarios.build_all_scenarios()
    
    print(f"\n{'='*60}")
    print("All scenarios built successfully!")
    print("Upload any scenario using:")
    print("  sudo ./goldbox_dual_upload.sh sja1110_uc_<scenario>.bin sja1110_switch_<scenario>.bin")

if __name__ == "__main__":
    main()