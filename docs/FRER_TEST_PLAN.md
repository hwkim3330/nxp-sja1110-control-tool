# Gold Box FRER 테스트 계획

## 하드웨어 구성
- **디바이스**: NXP S32G-VNP-GLDBOX
- **스위치**: SJA1110A (11포트 TSN 스위치)
- **프로세서**: S32G274A (PFE 및 GMAC 포함)

## 포트 매핑

### SJA1110 내부 포트 할당
```
Port 0: Reserved (내부용)
Port 1: P1/P4 커넥터 (100BASE-TX)
Port 2: P2A 커넥터 (1000BASE-T, AR8035 PHY 경유)
Port 3: P2B 커넥터 (1000BASE-T, AR8035 PHY 경유)
Port 4: PFE_MAC0 (S32G 내부 SGMII 연결)
Port 5-10: P6-P11 커넥터 (100BASE-T1, TJA1101 PHY)
```

### S32G 직접 연결 (SJA1110 경유하지 않음)
```
P3A: GMAC0 (1000BASE-T)
P3B: PFE_MAC2 (1000BASE-T)
P5: PFE_MAC1 (1000BASE-T)
```

## FRER 테스트 시나리오

### 시나리오 1: PFE → 외부 이중화
**목적**: S32G PFE에서 오는 트래픽을 이중화하여 신뢰성 확보

```
입력: PFE_MAC0 (Port 4)
복제: Port 2 (P2A), Port 3 (P2B)
제거: 외부 장치에서 수행
VLAN: 100
우선순위: 7
```

**테스트 방법**:
1. PFE_MAC0에서 테스트 패킷 전송
2. P2A와 P2B 모두에서 동일 패킷 수신 확인
3. 시퀀스 번호 확인

### 시나리오 2: 외부 → PFE 이중화
**목적**: 외부 트래픽을 이중 경로로 전송 후 PFE에서 중복 제거

```
입력: P2A (Port 2)
복제: Port 5 (P6), Port 6 (P7)
제거: PFE_MAC0 (Port 4)
VLAN: 200
우선순위: 6
```

**테스트 방법**:
1. P2A로 패킷 주입
2. P6, P7에서 복제된 패킷 확인
3. PFE_MAC0에서 단일 패킷만 수신 확인

### 시나리오 3: 100BASE-T1 링 이중화
**목적**: 차량용 이더넷 링 토폴로지에서 이중화

```
입력: P6 (Port 5)
복제: Port 6 (P7), Port 7 (P8)
제거: P10 (Port 9)
VLAN: 300
우선순위: 5
```

**테스트 방법**:
1. P6으로 CAN 게이트웨이 트래픽 시뮬레이션
2. P7, P8에서 복제 확인
3. P10에서 중복 제거 확인

### 시나리오 4: 중요 제어 메시지 삼중화
**목적**: 안전 critical 메시지의 삼중 이중화

```
입력: P1 (Port 1)
복제: Port 2 (P2A), Port 3 (P2B), Port 5 (P6)
제거: PFE_MAC0 (Port 4)
VLAN: 10
우선순위: 7 (최고)
```

**테스트 방법**:
1. P1으로 제어 메시지 전송
2. P2A, P2B, P6 모두에서 수신 확인
3. PFE에서 단일 메시지만 처리 확인

## 구성 파일

### 생성된 파일
- `goldbox_frer.bin`: SJA1110 스위치 구성 바이너리
- `goldbox_frer_testplan.json`: 테스트 시나리오 정의

### 업로드 방법

```bash
# 1. sysfs를 통한 업로드 (권장)
sudo cp goldbox_frer.bin /lib/firmware/
echo "goldbox_frer.bin" | sudo tee /sys/bus/spi/devices/spi0.0/switch-configuration/switch_cfg_upload

# 2. 업로드 도구 사용
sudo python3 sja1110_upload.py -r -c goldbox_frer.bin

# 3. 리셋 후 업로드
echo "1" | sudo tee /sys/bus/spi/devices/spi0.0/switch-configuration/switch_reset
sleep 1
echo "goldbox_frer.bin" | sudo tee /sys/bus/spi/devices/spi0.0/switch-configuration/switch_cfg_upload
```

## 검증 방법

### 1. 패킷 캡처
```bash
# P2A에서 캡처
sudo tcpdump -i eth0 -w p2a_capture.pcap

# P2B에서 캡처
sudo tcpdump -i eth1 -w p2b_capture.pcap
```

### 2. 시퀀스 번호 확인
- R-TAG (0xF1C1) 헤더의 시퀀스 번호 확인
- 중복 패킷의 동일 시퀀스 번호 확인

### 3. 통계 확인
```bash
# SJA1110 통계 읽기
cat /sys/bus/spi/devices/spi0.0/statistics/cb_stats
```

## 주의사항

1. **포트 검증**: P3A, P3B, P5는 S32G 직접 연결이므로 SJA1110 FRER에 사용 불가
2. **VLAN 설정**: 각 시나리오별 VLAN ID 충돌 방지
3. **우선순위**: Critical 트래픽은 우선순위 7 사용
4. **시퀀스 히스토리**: 기본 32개, 비디오는 64개 설정

## 트러블슈팅

### 문제: 패킷 복제 안됨
- CB 테이블 활성화 확인
- FRMREPEN 비트 설정 확인
- 포트 마스크 확인

### 문제: 중복 제거 안됨
- Individual Recovery 테이블 확인
- 시퀀스 히스토리 크기 확인
- 타임아웃 설정 확인

### 문제: 업로드 실패
- 바이너리 헤더 마커 (0x6AA6...) 확인
- CRC32 체크섬 확인
- 파일 크기 확인