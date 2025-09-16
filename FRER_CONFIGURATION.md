# FRER 구성 상세 설명

## FRER (Frame Replication and Elimination for Reliability) 동작 원리

### 📌 핵심 개념: 1개 입력 → 2개 이상 복제

FRER은 **하나의 프레임을 여러 경로로 복제**하여 전송하고, 수신측에서 **중복을 제거**하는 기술입니다.

```
[송신기] → [프레임] → [SJA1110 스위치]
                            ↓
                    [FRER 복제 엔진]
                       ↙        ↘
                  [경로 1]    [경로 2]
                       ↘        ↙
                    [수신측 스위치]
                            ↓
                    [중복 제거 엔진]
                            ↓
                        [수신기]
```

## Gold Box 포트 구성

### 물리적 포트 매핑 (검증)
```
SJA1110 Port | Gold Box 커넥터 | 타입         | 속도
-------------|------------------|--------------|--------
Port 1       | P1               | RJ45         | 100Mbps
Port 2       | P2A              | RJ45         | 1Gbps
Port 3       | P2B              | RJ45         | 1Gbps
Port 4       | PFE_MAC0         | Internal     | 1Gbps (SGMII)
Port 5       | P6               | 100BASE-T1   | 100Mbps
Port 6       | P7               | 100BASE-T1   | 100Mbps
Port 7       | P8               | 100BASE-T1   | 100Mbps
Port 8       | P9               | 100BASE-T1   | 100Mbps
Port 9       | P10              | 100BASE-T1   | 100Mbps
Port 10      | P11              | 100BASE-T1   | 100Mbps
```

주의: P3A(GMAC0), P3B(PFE_MAC2), P5(PFE_MAC1)는 SJA1110을 거치지 않는 직접 연결 포트로, FRER 적용 대상이 아닙니다. 자세한 구조는 `CORRECT_PORT_MAPPING.md`를 참고하세요.

## 구현된 FRER 시나리오

### 1️⃣ 테스트 시나리오 (test_scenario)
가장 포괄적인 테스트를 위한 구성:

```
Stream 1: PFE → P2A, P2B (VLAN 100)
- CPU에서 나온 트래픽을 두 개의 1G 포트로 복제
- 용도: 외부 네트워크로의 이중화된 전송

Stream 2: P2A → P6, P7 (VLAN 200)
- 외부 RJ45에서 들어온 트래픽을 T1 포트 2개로 복제
- 용도: RJ45 → 자동차 네트워크 브리지

Stream 3: P6 → P7, P8 (VLAN 300)
- T1 포트 간 링 토폴로지 구성
- 용도: 자동차 ECU 간 이중화

Stream 4: P1 → P2A, P2B, P6 (VLAN 10, Priority 7)
- 크리티컬 제어 메시지 3중 복제
- 용도: 안전-critical 메시지 전송
```

### 2️⃣ 기본 RJ45 복제 (basic_rj45)
```
Stream 1: P1 (100M) → P2A, P2B (1G)
- 100M 입력을 두 개의 1G 포트로 복제

Stream 2: P2A (1G) → P1, P3
- 1G 입력을 100M과 1G로 분산
```

### 3️⃣ RJ45 → 자동차 T1 (rj45_to_automotive)
```
Stream 1: P2A → P6, P7, P8, P9 (4중 복제)
- RJ45 입력을 4개 T1으로 브로드캐스트

Stream 2: P1 → P6, P7
- 100M 입력을 T1 페어로 복제

Stream 3: P3 → P8, P9, P10
- 1G 입력을 T1 3개로 복제
```

## FRER 바이너리 구조

### sja1110_switch.bin (655,404 bytes)
```
오프셋        | 내용                    | 크기
-------------|------------------------|--------
0x000000     | IMAGE_VALID_MARKER     | 8 bytes
0x000008     | DEVICE_ID (0xb700030e) | 4 bytes
0x00000C     | Configuration Flags    | 4 bytes
0x034000     | General Parameters     |
             | - FRMREPEN (enable)    | 4 bytes
0x080000     | CB Sequence Gen Table  |
             | - Stream replication   | N entries
0x090000     | CB Individual Recovery |
             | - Duplicate elimination| N entries
0x0A0000     | DPI Table              |
             | - Stream identification| N entries
0x0A002C     | CRC32 Checksum         | 4 bytes
```

### CB Sequence Generation Entry (복제 설정)
```c
struct cb_seq_gen {
    uint16_t stream_handle;  // 스트림 ID
    uint16_t port_mask;      // 복제할 포트 비트마스크
    uint8_t  flags;          // 0x80 = enabled
    uint16_t seq_num;        // 시퀀스 번호
};
```

예시: Stream 1을 Port 2,3으로 복제
- port_mask = 0x000C (비트 2,3 설정)
- 0000 0000 0000 1100 = Port 2,3 활성화

### CB Individual Recovery Entry (중복 제거)
```c
struct cb_ind_recovery {
    uint16_t stream_handle;  // 스트림 ID
    uint8_t  ingress_port;   // 입력 포트
    uint8_t  flags;          // 0x80 = enabled
    uint16_t seq_num;        // 현재 시퀀스
    uint16_t history_len;    // 히스토리 크기 (32)
    uint16_t reset_timeout;  // 타임아웃 (100ms)
};
```

## 실제 동작 예시

### 예시 1: PFE → 외부 이중화
```bash
# PFE에서 ping 전송
ping -I pfe0 192.168.1.100

# 결과:
# - 같은 ICMP 패킷이 P2A와 P2B 모두에서 출력
# - 각 패킷에 R-TAG (0xF1C1) 헤더와 시퀀스 번호 추가
# - 수신측에서 첫 번째 도착 패킷만 처리, 중복 폐기
```

### 예시 2: 외부 → PFE with 중복 제거
```bash
# P2A와 P2B에서 동시에 같은 패킷 전송
# (실제로는 송신측 스위치가 자동 복제)

# PFE에서 수신:
# - 두 경로로 도착한 중복 패킷 중 하나만 수신
# - CB Individual Recovery가 시퀀스 번호로 중복 탐지
```

## 테스트 방법

### 1. FRER 바이너리 생성 및 업로드
```bash
# 테스트 시나리오로 바이너리 생성
./frer test

# Gold Box에 업로드
sudo ./goldbox_dual_upload.sh sja1110_uc.bin sja1110_switch.bin
```

### 2. 트래픽 모니터링
```bash
# 복제 확인 (두 포트에서 동시 캡처)
sudo tcpdump -i sw0p2 -e -n &
sudo tcpdump -i sw0p3 -e -n &

# R-TAG 헤더 확인 (0xF1C1)
sudo tcpdump -i sw0p2 -e -n -XX | grep -A2 "f1c1"
```

### 3. 통계 확인
```bash
# FRER 통계
cat /sys/bus/spi/devices/spi0.0/switch-configuration/cb_stats

# 포트별 패킷 카운터
for i in {0..10}; do
    echo "Port $i: $(cat /sys/class/net/sw0p$i/statistics/rx_packets 2>/dev/null || echo 'N/A')"
done
```

## 주의사항

1. **Gold Box는 복제만 수행**: 중복 제거는 수신 장치에서 구현 필요
2. **시퀀스 번호 관리**: 각 스트림별로 독립적인 시퀀스 번호 사용
3. **VLAN 분리**: 각 FRER 스트림은 고유한 VLAN ID 사용 권장
4. **히스토리 크기**: 기본 32, 비디오는 64 권장
5. **타임아웃**: 100ms 후 시퀀스 리셋

## 파일 다운로드

생성된 바이너리 파일:
- `sja1110_uc.bin` - 마이크로컨트롤러 펌웨어
- `sja1110_switch.bin` - 스위치 FRER 구성
- `goldbox_frer_testplan.json` - 구성 정보 (JSON)

이 파일들은 `/home/kim/nxp-sja1110-control-tool/` 디렉토리에 있습니다.
