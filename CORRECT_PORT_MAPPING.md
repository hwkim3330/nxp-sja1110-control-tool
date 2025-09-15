# Gold Box 정확한 포트 매핑 및 FRER 구성

## ⚠️ 중요: P3A, P3B, P5는 SJA1110을 거치지 않음!

### 실제 하드웨어 연결 구조

```
┌─────────────────────────────────────────────────────────┐
│                     S32G274A                            │
│                                                         │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
│  │ GMAC0  │  │PFE_MAC0│  │PFE_MAC1│  │PFE_MAC2│      │
│  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘      │
│      │           │ SGMII      │           │            │
└──────┼───────────┼────────────┼───────────┼────────────┘
       │           │            │           │
       │           ↓            │           │
       │    ┌──────────┐        │           │
       │    │ SJA1110  │        │           │
       │    │  Port 4  │        │           │
       │    │          │        │           │
       │    │ Port 2→P2A        │           │
       │    │ Port 3→P2B        │           │
       │    │ Port 1→P1         │           │
       │    └──────────┘        │           │
       │                        │           │
       ↓                        ↓           ↓
     [P3A]                    [P5]        [P3B]
   (직접연결)               (직접연결)   (직접연결)
```

## 📌 올바른 포트 매핑

### SJA1110 스위치 포트 (FRER 가능)
| SJA1110 Port | 물리 커넥터 | 설명 | FRER 지원 |
|--------------|------------|------|-----------|
| Port 0 | - | Reserved | ❌ |
| Port 1 | P1/P4 | 100BASE-TX | ✅ |
| Port 2 | P2A | 1000BASE-T (AR8035 PHY) | ✅ |
| Port 3 | P2B | 1000BASE-T (AR8035 PHY) | ✅ |
| Port 4 | PFE_MAC0 | S32G 내부 SGMII | ✅ |
| Port 5 | P6 | 100BASE-T1 | ✅ |
| Port 6 | P7 | 100BASE-T1 | ✅ |
| Port 7 | P8 | 100BASE-T1 | ✅ |
| Port 8 | P9 | 100BASE-T1 | ✅ |
| Port 9 | P10 | 100BASE-T1 | ✅ |
| Port 10 | P11 | 100BASE-T1 | ✅ |

### S32G 직접 연결 (FRER 불가능)
| S32G 인터페이스 | 물리 커넥터 | 설명 | FRER 지원 |
|----------------|------------|------|-----------|
| GMAC0 | P3A | 1000BASE-T (KSZ9031 PHY) | ❌ |
| PFE_MAC1 | P5 | 1000BASE-T | ❌ |
| PFE_MAC2 | P3B | 1000BASE-T (KSZ9031 PHY) | ❌ |

## 🔄 올바른 FRER 복제 시나리오

### ✅ 가능한 시나리오

#### 1. PFE → 외부 이중화 (가장 일반적)
```
입력: PFE_MAC0 (Port 4)
복제: Port 2 (P2A), Port 3 (P2B)
```
```python
# 올바른 구성
add_stream(id=1, src_port=4, dst_ports=[2, 3])  # PFE → P2A, P2B
```

#### 2. 외부 → 내부 이중화
```
입력: P2A (Port 2)
복제: Port 4 (PFE), Port 5 (P6)
```
```python
# 올바른 구성
add_stream(id=2, src_port=2, dst_ports=[4, 5])  # P2A → PFE, P6
```

#### 3. P1 → 다중 포트
```
입력: P1 (Port 1)
복제: Port 2 (P2A), Port 3 (P2B), Port 5 (P6)
```
```python
# 올바른 구성
add_stream(id=3, src_port=1, dst_ports=[2, 3, 5])  # P1 → P2A, P2B, P6
```

### ❌ 불가능한 시나리오 (P3A, P3B, P5 관련)

```python
# 잘못된 구성 - P3B는 SJA1110을 거치지 않음!
# add_stream(id=X, src_port='P3B', dst_ports=['P2A', 'P2B'])  # 불가능!

# 잘못된 구성 - P3A는 직접 연결
# add_stream(id=X, src_port='P3A', dst_ports=[...])  # 불가능!

# 잘못된 구성 - P5는 직접 연결
# add_stream(id=X, src_port='P5', dst_ports=[...])  # 불가능!
```

## 🎯 권장 테스트 구성

### 테스트 1: 기본 이중화
```bash
./frer add-stream --stream-id 1 \
  --src-port 4 \
  --dst-ports 2 3 \
  --name "PFE_to_P2AB"
```

### 테스트 2: T1 브리지
```bash
./frer add-stream --stream-id 2 \
  --src-port 2 \
  --dst-ports 5 6 7 \
  --name "P2A_to_T1"
```

### 테스트 3: 크리티컬 3중화
```bash
./frer add-stream --stream-id 3 \
  --src-port 1 \
  --dst-ports 2 3 5 \
  --name "P1_Critical"
```

## 📊 포트 번호 정리

```python
# 올바른 포트 번호 매핑
PORT_MAP = {
    'PFE': 4,      # PFE_MAC0 (SGMII)
    'P1': 1,       # 100BASE-TX
    'P2A': 2,      # 1000BASE-T
    'P2B': 3,      # 1000BASE-T
    # 'P3A': X,    # 사용 불가 (GMAC0 직접)
    # 'P3B': X,    # 사용 불가 (PFE_MAC2 직접)
    # 'P5': X,     # 사용 불가 (PFE_MAC1 직접)
    'P6': 5,       # 100BASE-T1
    'P7': 6,       # 100BASE-T1
    'P8': 7,       # 100BASE-T1
    'P9': 8,       # 100BASE-T1
    'P10': 9,      # 100BASE-T1
    'P11': 10      # 100BASE-T1
}
```

## 🔍 검증 방법

### 1. 포트 상태 확인
```bash
# SJA1110 관리 포트만 확인
for i in 1 2 3 4 5 6 7 8 9 10; do
  echo "Port $i: $(cat /sys/class/net/sw0p$i/carrier 2>/dev/null)"
done

# P3A, P3B, P5는 별도 인터페이스
ip link show | grep -E "eth[0-9]|gmac|pfe"
```

### 2. FRER 트래픽 테스트
```bash
# PFE에서 트래픽 생성
ping -I pfe0 192.168.1.100

# P2A, P2B에서 복제 확인
tcpdump -i eth0 -e -n  # P2A
tcpdump -i eth1 -e -n  # P2B
```

## ⚠️ 주의사항

1. **P3A, P3B, P5는 FRER 불가능** - S32G에 직접 연결되어 SJA1110 스위치를 거치지 않음
2. **PFE_MAC0 (Port 4)가 주요 입력** - S32G CPU 트래픽이 여기로 들어옴
3. **Port 2, 3이 주요 출력** - P2A, P2B로 외부 네트워크 연결
4. **Port 1은 100Mbps 제한** - P1/P4는 100BASE-TX
5. **Port 5-10은 자동차용** - 100BASE-T1 automotive Ethernet

## 📝 요약

- ✅ **사용 가능**: Port 1-10 (P1, P2A, P2B, P6-P11, PFE_MAC0)
- ❌ **사용 불가능**: P3A, P3B, P5 (S32G 직접 연결)
- 🎯 **주요 경로**: PFE_MAC0 (Port 4) → P2A (Port 2), P2B (Port 3)