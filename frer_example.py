#!/usr/bin/env python3
"""
FRER 사용 예제
Gold Box에서 프레임 복제 구성하는 방법
"""

import subprocess
import sys

def run_command(cmd):
    """명령 실행 및 출력"""
    print(f"\n실행: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"에러: {result.stderr}")
    return result.returncode == 0

def main():
    print("=" * 60)
    print("Gold Box FRER 구성 예제")
    print("=" * 60)

    print("\n### 1. 간단한 복제 설정 ###")
    print("Port 1에서 입력 → Port 2, 3으로 복제")

    commands = [
        # FRER 활성화
        "./frer enable",

        # 스트림 추가: P1 → P2A, P2B
        "./frer add-stream --stream-id 1 --src-port P1 --dst-ports P2A P2B --vlan-id 100",

        # 상태 확인
        "./frer status",

        # 바이너리 생성
        "./frer generate-binary --output simple_frer.bin"
    ]

    for cmd in commands:
        if not run_command(cmd):
            print(f"명령 실패: {cmd}")
            sys.exit(1)

    print("\n### 2. 복잡한 시나리오 ###")
    print("여러 스트림 동시 구성")

    # 새로운 인스턴스로 시작
    run_command("./frer enable")

    # 여러 스트림 추가
    streams = [
        # PFE → 외부 이중화
        {
            'id': 1,
            'src': 'PFE',
            'dst': ['P2A', 'P2B'],
            'vlan': 100,
            'desc': 'CPU to External'
        },
        # 외부 → T1 네트워크
        {
            'id': 2,
            'src': 'P2A',
            'dst': ['P6', 'P7', 'P8'],
            'vlan': 200,
            'desc': 'External to T1'
        },
        # 크리티컬 메시지 3중화
        {
            'id': 3,
            'src': 'P1',
            'dst': ['P2A', 'P2B', 'P6'],
            'vlan': 10,
            'desc': 'Critical Triple'
        }
    ]

    for stream in streams:
        cmd = (f"./frer add-stream --stream-id {stream['id']} "
               f"--src-port {stream['src']} "
               f"--dst-ports {' '.join(stream['dst'])} "
               f"--vlan-id {stream['vlan']} "
               f"--name '{stream['desc']}'")
        run_command(cmd)

    # 최종 상태 확인
    run_command("./frer status")

    # 구성 저장
    run_command("./frer save --file complex_config.json")
    run_command("./frer generate-binary --output complex_frer.bin")

    print("\n### 3. 사전 정의된 시나리오 사용 ###")

    scenarios = [
        'basic_rj45',
        'rj45_to_automotive',
        'redundant_gateway',
        'ring_topology'
    ]

    for scenario in scenarios:
        print(f"\n시나리오: {scenario}")
        run_command(f"./frer scenario --scenario {scenario}")
        run_command(f"./frer generate-binary --output {scenario}.bin")

    print("\n" + "=" * 60)
    print("완료! 생성된 파일:")
    print("- simple_frer.bin : 간단한 복제 구성")
    print("- complex_frer.bin : 복잡한 다중 스트림")
    print("- complex_config.json : 구성 저장 파일")
    print("- basic_rj45.bin : 기본 RJ45 시나리오")
    print("- rj45_to_automotive.bin : RJ45-T1 브리지")
    print("- redundant_gateway.bin : 이중화 게이트웨이")
    print("- ring_topology.bin : 링 토폴로지")
    print("\n업로드: sudo ./goldbox_dual_upload.sh sja1110_uc.bin <config>.bin")
    print("=" * 60)

if __name__ == "__main__":
    main()