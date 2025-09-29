# NXP SJA1110 Gold Box FRER Control Tool

**IEEE 802.1CB Frame Replication and Elimination for Reliability (FRER) 구성 도구**

NXP S32G-VNP-GLDBOX (Gold Box)의 SJA1110 TSN 스위치에서 FRER 프레임 복제 기능을 구성하는 완전한 솔루션입니다.

## 🚀 주요 기능

- **다중 FRER 시나리오**: 6가지 사전 구성된 RJ45 입력 복제 시나리오
- **듀얼 펌웨어**: `sja1110_uc.bin` (마이크로컨트롤러) + `sja1110_switch.bin` (스위치 구성)
- **실제 포트 매핑**: Gold Box의 물리적 포트와 정확한 매칭
- **자동 업로드**: Gold Box 펌웨어 업로드 스크립트 포함
- **포괄적 테스트**: FRER 기능 검증 도구
- **CRC32 자동 처리**: 생성된 모든 바이너리에 올바른 헤더와 CRC32 트레일러 자동 삽입
- **기본 설정 유지**: `config/base_switch_words.json`에서 추출한 NXP 기본 스위치 설정을 그대로 오버레이한 뒤 FRER 항목만 추가 구성

## 📋 목차

- [하드웨어 요구사항](#하드웨어-요구사항)
- [포트 매핑](#포트-매핑)
- [FRER 시나리오](#frer-시나리오)
- [설치 및 사용법](#설치-및-사용법)
- [테스트 방법](#테스트-방법)
- [문제 해결](#문제-해결)
- [부록: 펌웨어 메모리 맵](docs/SJA1110_Firmware_Format.md)

## 🔧 하드웨어 요구사항

### 필수 하드웨어
- **NXP S32G-VNP-GLDBOX** (Gold Box)
- **SJA1110A TSN 스위치** (11포트)
- **S32G274A 프로세서** (PFE 포함)

### 연결 인터페이스
- **RJ45 포트**: P1 (100M), P2A/P2B (1G), P3A/P3B (1G, SJA1110 미경유)
- **100BASE-T1 포트**: P6-P11 (자동차용 이더넷)
- **내부 연결**: S32G PFE (CPU 인터페이스)

## 🔌 포트 매핑 (검증됨)

중요: P3A/P3B, P5는 SJA1110 스위치를 거치지 않습니다. FRER는 SJA1110 경유 포트에서만 적용됩니다. 자세한 도식은 `CORRECT_PORT_MAPPING.md` 참고.

| SJA1110 Port | Physical | Type | Speed | 설명 |
|--------------|----------|------|-------|------|
| Port 1 | P1 | RJ45 | 100M | 100BASE-TX |
| Port 2 | P2A | RJ45 | 1G | 1000BASE-T |
| Port 3 | P2B | RJ45 | 1G | 1000BASE-T |
| Port 4 | PFE_MAC0 | Internal | 1G | S32G CPU (SGMII) |
| Port 5 | P6 | T1 | 100M | 100BASE-T1 |
| Port 6 | P7 | T1 | 100M | 100BASE-T1 |
| Port 7 | P8 | T1 | 100M | 100BASE-T1 |
| Port 8 | P9 | T1 | 100M | 100BASE-T1 |
| Port 9 | P10 | T1 | 100M | 100BASE-T1 |
| Port 10 | P11 | T1 | 100M | 100BASE-T1 |

직접 연결(스위치 미경유, FRER 불가): P3A(GMAC0), P3B(PFE_MAC2), P5(PFE_MAC1)

## 🎯 FRER 시나리오

### 1. 기본 RJ45 복제 (`basic_rj45`)
**용도**: 기본적인 이더넷 포트 간 복제
```
P1 (100M) → P2A, P2B (1G)    # 업링크 복제
P2A (1G)  → P1, P3           # 다운링크 분산
```

### 2. RJ45 → 자동차 T1 (`rj45_to_automotive`)
**용도**: RJ45 이더넷과 자동차 T1 네트워크 브리지
```
P2A (1G)  → P6, P7, P8, P9 (T1)  # 브로드캐스트
P1 (100M) → P6, P7 (T1)          # 페어 복제
P3 (1G)   → P8, P9, P10 (T1)     # 고속 복제
```

### 3. 이중화 게이트웨이 (`redundant_gateway`)
**용도**: 고가용성 게이트웨이 with 백업 경로
```
P2A (External) → PFE, P6 (T1 백업)    # 이중화 입력
PFE            → P2A, P2B              # 이중 RJ45 출력
P1 (Control)   → All Major Ports       # 크리티컬 제어
```

### 4. 링 토폴로지 (`ring_topology`)
**용도**: 링 네트워크 이중화
```
P2A (Ring in)  → P2B (Ring out), P6 (T1)  # 양방향 복제
P6 (T1 in)     → P7, P8 (T1 ring)          # T1 링
P8 (T1 backup) → P1, P3 (RJ45 백업)        # 백업 경로
```

### 5. 로드 밸런싱 (`load_balancing`)
**용도**: 트래픽 로드 분산
```
P2A (1G)       → P1, P3, P6, P7     # 고속 분산
P2B (Premium)  → PFE, P2A, P8, P9   # 프리미엄 복제
```

### 6. 자동차 혼합 네트워크 (`mixed_automotive`)
**용도**: 자동차 ECU 네트워크 with 진단
```
P1 (Diagnostic) → P6, P7, P8 (ECU T1)          # 진단 → ECU
P6 (Sensors)    → PFE, P2A                     # 센서 집계
PFE (Safety)    → All External Ports           # 안전 브로드캐스트
```

## 🛠 설치 및 사용법

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/nxp-sja1110-control-tool.git
cd nxp-sja1110-control-tool
```

### 2. 의존성 설치
```bash
# Python 패키지
pip3 install --break-system-packages scapy netifaces

# 시스템 패키지 (Ubuntu/Debian)
sudo apt update
sudo apt install python3-dev build-essential
```

### 3. 시나리오 빌드
```bash
# 모든 시나리오 빌드
python3 src/sja1110_rj45_scenarios.py

# 또는 개별 시나리오
python3 src/sja1110_dual_firmware.py
```

### 4. Gold Box에 업로드
```bash
# 권장: 검증된 릴리스 바이너리 사용
cd binaries_release/latest
sudo ../../goldbox_dual_upload.sh sja1110_uc.bin sja1110_switch.bin

# VLAN 태그 버전을 사용하려면 (tagged 100)
sudo ../../goldbox_dual_upload.sh ../2025-09-29-multi/sja1110_uc_p4_to_p2ab.bin \
                                     ../2025-09-29-multi/sja1110_switch_p4_to_p2ab.bin
```

### 4-1. 수동(sysfs) 업로드 (대안)
```bash
sudo cp binaries_release/latest/*.bin /lib/firmware/

# 순서: 스위치 → UC
echo sja1110_switch.bin | sudo tee /sys/bus/spi/devices/spi0.0/switch-configuration/switch_cfg_upload
echo sja1110_uc.bin | sudo tee /sys/bus/spi/devices/spi0.1/uc-configuration/uc_fw_upload
```

### ✅ CRC32 검증/재계산

펌웨어 파일을 편집한 뒤에는 마지막 4바이트 CRC32 트레일러를 반드시 갱신해야 합니다. 저장소에 포함된 `tools/fix_crc.py`를 사용하면 쉽게 재계산할 수 있습니다.

```bash
# 여러 바이너리를 한 번에 검증 및 갱신
./tools/fix_crc.py sja1110_switch.bin sja1110_uc.bin
# 출력 예: "✓ Updated sja1110_switch.bin CRC32 to 0xXXXXXXXX"
```

자세한 메모리 구조는 [`docs/SJA1110_Firmware_Format.md`](docs/SJA1110_Firmware_Format.md)를 참고하세요.

## 🧪 테스트 방법

### 1. FRER 기능 테스트
```bash
# 테스트 스크립트 실행 (root 권한 필요)
sudo python3 test_frer_goldbox.py
```

### 2. 트래픽 생성 및 모니터링
```bash
# 패킷 캡처 (복제 확인)
tcpdump -i sw0p2 -v &
tcpdump -i sw0p3 -v &

# 테스트 트래픽 송신
ping -I pfe0 192.168.1.100

# 또는 scapy 테스트
python3 -c "
from scapy.all import *
pkt = Ether()/IP(dst='192.168.1.100')/ICMP()
sendp(pkt, iface='pfe0', count=10)
"
```

### 3. FRER 통계 확인
```bash
# FRER 상태 확인
cat /sys/bus/spi/devices/spi0.0/switch-configuration/frer_status

# 포트 상태 확인
for port in /sys/class/net/sw0p*; do
  echo "$(basename $port): $(cat $port/carrier 2>/dev/null || echo unknown)"
done
```

## 📊 시나리오 선택 가이드

| 사용 목적 | 추천 시나리오 | 특징 |
|-----------|---------------|------|
| **기본 네트워킹** | `basic_rj45` | 단순한 RJ45 포트 간 복제 |
| **자동차 게이트웨이** | `rj45_to_automotive` | RJ45 ↔ T1 브리지 |
| **고가용성 시스템** | `redundant_gateway` | 백업 경로 포함 |
| **링 네트워크** | `ring_topology` | 링 토폴로지 지원 |
| **고성능 시스템** | `load_balancing` | 로드 분산 |
| **자동차 ECU** | `mixed_automotive` | ECU 네트워크 최적화 |

## 📁 파일 구조

```
nxp-sja1110-control-tool/
├── src/
│   ├── sja1110_dual_firmware.py      # 기본 듀얼 펌웨어 빌더
│   ├── sja1110_rj45_scenarios.py     # 다중 시나리오 빌더
│   ├── sja1110_driver.py             # 하드웨어 드라이버
│   └── goldbox_frer_config.py        # FRER 구성 도구
├── config/
│   └── frer_example.json             # 구성 예제
├── docs/
│   ├── FRER_TEST_PLAN.md             # 테스트 계획
│   └── goldbox_port_mapping.md       # 포트 매핑 상세
├── goldbox_dual_upload.sh            # 펌웨어 업로드 스크립트
├── test_frer_goldbox.py              # FRER 테스트 스크립트
└── README.md                         # 이 파일
```

## 🐛 문제 해결

### 1. 업로드 실패
```bash
# 드라이버 상태 확인
systemctl status sja1110

# 수동 드라이버 재시작
sudo systemctl stop sja1110
sudo systemctl start sja1110

# 장치 ID 확인
cat /sys/bus/spi/devices/spi0.0/device_id
```

### 2. 포트 인식 안됨
```bash
# 네트워크 인터페이스 확인
ip link show

# 스위치 포트 확인
ls /sys/class/net/sw0p*

# 물리적 연결 확인
for port in /sys/class/net/sw0p*; do
  ethtool $(basename $port) 2>/dev/null | grep "Link detected"
done
```

### 3. FRER 작동 안함
```bash
# FRER 구성 확인
python3 -c "
import json
with open('sja1110_firmware_config.json') as f:
    config = json.load(f)
print(f\"Streams: {config['frer_configuration']['streams']}\")
for stream in config['frer_configuration']['stream_details']:
    print(f\"  {stream['name']}: {stream['src_port']} → {stream['dst_ports']}\")
"

# CB 테이블 확인 (가능한 경우)
cat /sys/bus/spi/devices/spi0.0/switch-configuration/cb_table 2>/dev/null || echo "CB table not accessible"
```

## 🔍 고급 사용법

### 커스텀 시나리오 생성
```python
from src.sja1110_dual_firmware import SJA1110FirmwareBuilder

# 새 시나리오 빌더 생성
builder = SJA1110FirmwareBuilder()

# 복제 스트림 추가
builder.add_frer_replication_stream(
    stream_id=1,
    src_port=2,         # P2A
    dst_ports=[5, 6],   # P6, P7
    vlan_id=100,
    priority=7,
    name="Custom_Scenario"
)

# 펌웨어 생성
uc_fw = builder.build_microcontroller_firmware()
switch_cfg = builder.build_switch_firmware()

# 파일 저장
with open('custom_uc.bin', 'wb') as f:
    f.write(uc_fw)
with open('custom_switch.bin', 'wb') as f:
    f.write(switch_cfg)
```

### VLAN 및 우선순위 구성
- **VLAN ID**: 각 FRER 스트림별 고유 VLAN 할당
- **Priority**: 0 (낮음) ~ 7 (높음), 크리티컬 트래픽은 7 사용
- **R-TAG**: FRER 식별 태그 (0xF1C1 고정)

## 📚 참고 자료

- [IEEE 802.1CB-2017 FRER 표준](https://standards.ieee.org/standard/802_1CB-2017.html)
- [NXP SJA1110 데이터시트](https://www.nxp.com/products/interfaces/ethernet/automotive-ethernet-switches/sja1110-automotive-ethernet-switch:SJA1110)
- [TSN 시간 민감 네트워킹 개요](https://en.wikipedia.org/wiki/Time-Sensitive_Networking)
- [NXP automotive SJA1110 Linux driver (nxp-archive)](https://github.com/nxp-archive/autoivnsw_sja1110_linux)
- [openil_sja1105-tool (SJA1105/1110 configuration utilities)](https://github.com/nxp-archive/openil_sja1105-tool)
- [NXP Community: S32G2 Linux BSP & SJA1110 토론](https://community.nxp.com/t5/S32G/S32G2-LINUX-BSP-and-SJA1110/m-p/1985342)

## 🤝 기여하기

1. 이 저장소를 Fork
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## ⚠️ 주의사항

- **Gold Box는 FRER 복제만 수행**: 중복 제거는 수신측에서 구현 필요
- **루트 권한 필요**: 펌웨어 업로드와 네트워크 테스트는 sudo 권한 필요
- **하드웨어 호환성**: NXP S32G-VNP-GLDBOX 전용
- **테스트 환경**: 실제 네트워크 연결 후 테스트 권장

---

**Created by**: TSN Performance Testing Team  
**Contact**: 이슈 또는 질문이 있으시면 GitHub Issues를 이용해주세요.
## ⚡ Quick Start (Clean)
- Recommended (untagged):
  - `cd binaries_release/latest`
  - `sudo ../../tools/apply_frer.sh sja1110_uc.bin sja1110_switch.bin`
- More scenarios: `binaries_release/2025-09-29-multi` (tagged/untagged). See `SCENARIOS.md`.
- Details: `RELEASE_NOTES.md`.
