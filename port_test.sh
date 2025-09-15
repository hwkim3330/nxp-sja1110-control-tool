#!/bin/bash
#
# Gold Box FRER 포트 테스트 스크립트
# 각 포트별 복제 동작 확인
#

echo "========================================="
echo "Gold Box FRER 포트별 테스트"
echo "========================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "\n${BLUE}포트 구성:${NC}"
echo "┌─────────┬──────────┬─────────────┬──────────┐"
echo "│ Port    │ Connector│ Type        │ Speed    │"
echo "├─────────┼──────────┼─────────────┼──────────┤"
echo "│ Port 0  │ PFE      │ S32G CPU    │ 1Gbps    │"
echo "│ Port 1  │ P1       │ RJ45        │ 100Mbps  │"
echo "│ Port 2  │ P2A      │ RJ45        │ 1Gbps    │"
echo "│ Port 3  │ P2B      │ RJ45        │ 1Gbps    │"
echo "│ Port 4  │ P3       │ RJ45        │ 1Gbps    │"
echo "│ Port 5  │ P6       │ 100BASE-T1  │ 100Mbps  │"
echo "│ Port 6  │ P7       │ 100BASE-T1  │ 100Mbps  │"
echo "│ Port 7  │ P8       │ 100BASE-T1  │ 100Mbps  │"
echo "│ Port 8  │ P9       │ 100BASE-T1  │ 100Mbps  │"
echo "│ Port 9  │ P10      │ 100BASE-T1  │ 100Mbps  │"
echo "│ Port 10 │ P11      │ 100BASE-T1  │ 100Mbps  │"
echo "└─────────┴──────────┴─────────────┴──────────┘"

echo -e "\n${GREEN}테스트 1: PFE → P2A, P2B 복제${NC}"
echo "CPU에서 나온 패킷을 두 개의 1G 포트로 복제"
echo "명령: ./frer add-stream --stream-id 1 --src-port PFE --dst-ports P2A P2B"
echo ""
echo "테스트 방법:"
echo "1. tcpdump -i sw0p2 -e -n &"
echo "2. tcpdump -i sw0p3 -e -n &"
echo "3. ping -I pfe0 192.168.1.100"
echo "결과: 두 포트 모두에서 동일한 ICMP 패킷 관찰"

echo -e "\n${GREEN}테스트 2: P1 → P2A, P2B, P6 삼중 복제${NC}"
echo "100M 포트에서 입력된 크리티컬 메시지를 3개 포트로 복제"
echo "명령: ./frer add-stream --stream-id 2 --src-port P1 --dst-ports P2A P2B P6"
echo ""
echo "포트 마스크 계산:"
echo "  P2A(Port2) = bit 2 = 0x0004"
echo "  P2B(Port3) = bit 3 = 0x0008"
echo "  P6(Port5)  = bit 5 = 0x0020"
echo "  Total mask = 0x002C (비트: 00101100)"

echo -e "\n${GREEN}테스트 3: P2A → P6, P7, P8, P9 (RJ45 → T1)${NC}"
echo "외부 RJ45에서 자동차 T1 네트워크로 브로드캐스트"
echo "명령: ./frer add-stream --stream-id 3 --src-port P2A --dst-ports P6 P7 P8 P9"

echo -e "\n${YELLOW}FRER 동작 확인 명령어:${NC}"
echo "# 포트 상태 확인"
echo "for i in {0..10}; do"
echo "  echo \"Port \$i: \$(cat /sys/class/net/sw0p\$i/carrier 2>/dev/null || echo 'N/A')\""
echo "done"
echo ""
echo "# FRER 통계"
echo "cat /sys/bus/spi/devices/spi0.0/switch-configuration/cb_stats"
echo ""
echo "# 패킷 카운터"
echo "watch -n 1 'for i in {2..3}; do"
echo "  echo \"sw0p\$i RX: \$(cat /sys/class/net/sw0p\$i/statistics/rx_packets 2>/dev/null)\""
echo "done'"

echo -e "\n${BLUE}R-TAG 헤더 구조:${NC}"
echo "┌──────────────┬──────────────┬─────────────┬──────────────┐"
echo "│ EtherType    │ Reserved     │ Sequence    │ Original     │"
echo "│ 0xF1C1 (2B)  │ (6 bits)     │ Number (10b)│ EtherType(2B)│"
echo "└──────────────┴──────────────┴─────────────┴──────────────┘"
echo ""
echo "패킷 예시:"
echo "[Ethernet Header][0xF1C1][Seq:0001][Original Type][Payload]"

echo -e "\n${YELLOW}트래픽 생성 예제:${NC}"
cat << 'EOF'
# Python으로 테스트 패킷 생성
python3 << 'SCRIPT'
from scapy.all import *
import time

# FRER 테스트 패킷 생성
for i in range(10):
    # 일반 이더넷 프레임
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/IP(dst="192.168.1.100")/ICMP()

    # PFE 인터페이스로 전송
    sendp(pkt, iface="pfe0", verbose=False)
    print(f"Sent packet {i+1}")
    time.sleep(0.5)
SCRIPT
EOF

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}테스트 준비 완료!${NC}"
echo -e "${GREEN}=========================================${NC}"