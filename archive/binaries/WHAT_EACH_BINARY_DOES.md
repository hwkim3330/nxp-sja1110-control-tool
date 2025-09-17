# 각 바이너리가 하는 일

## 🎯 빠른 선택 가이드

| 원하는 기능 | 사용할 바이너리 | 복제 경로 |
|------------|----------------|----------|
| **기본 테스트** | `test_scenario` | PFE → P2A, P2B |
| **최대 부하 테스트** | `maximum_replication` | PFE → 모든 포트 (10개) |
| **안전 중요 시스템** | `triple_redundancy` | 3중 복제 |
| **간단한 이중화** | `dual_path` | 2개 경로 |
| **RJ45 ↔ T1 연결** | `rj45_to_automotive` | RJ45 → T1 포트들 |

---

## 📋 각 시나리오 상세 설명

### 1️⃣ **test_scenario** (⭐ 추천)
```
무엇: 종합 테스트 구성
입력 → 출력:
  - Stream 1: PFE (Port 4) → P2A (Port 2), P2B (Port 3)
  - Stream 2: P2A (Port 2) → P6 (Port 5), P7 (Port 6)
  - Stream 3: P6 (Port 5) → P7 (Port 6), P8 (Port 7)
  - Stream 4: P1 (Port 1) → P2A, P2B, P6
용도: 모든 기능 테스트
```

### 2️⃣ **basic_rj45**
```
무엇: 가장 간단한 RJ45 복제
입력 → 출력:
  - Stream 1: P1 (100M) → P2A (1G), P2B (1G)
  - Stream 2: P2A → P1, PFE
용도: 기본 동작 확인
```

### 3️⃣ **maximum_replication**
```
무엇: 최대 복제 스트레스 테스트
입력 → 출력:
  - Stream 1: PFE → 모든 포트 (P1~P11)
  - Stream 2: P2A → 나머지 모든 포트
용도: 최대 부하 테스트
```

### 4️⃣ **triple_redundancy**
```
무엇: 3중 이중화 (안전 critical)
입력 → 출력:
  - Stream 1: PFE → P2A, P2B, P1 (3중)
  - Stream 2: P1 → P6, P7, P8 (3중)
  - Stream 3: P2A → P9, P10, P11 (3중)
용도: 고신뢰성 시스템
```

### 5️⃣ **dual_path**
```
무엇: 간단한 2중 경로
입력 → 출력:
  - Stream 1: PFE → P2A, P2B
  - Stream 2: P1 → P6, P7
용도: 기본 이중화
```

### 6️⃣ **rj45_to_automotive**
```
무엇: RJ45를 자동차 T1으로 변환
입력 → 출력:
  - Stream 1: P2A → P6, P7, P8, P9 (4개 T1)
  - Stream 2: P1 → P6, P7
  - Stream 3: PFE → P8, P9, P10
용도: 이더넷-자동차 브리지
```

### 7️⃣ **redundant_gateway**
```
무엇: 이중화 게이트웨이
입력 → 출력:
  - Stream 1: P2A → PFE, P6 (백업 포함)
  - Stream 2: PFE → P2A, P2B
  - Stream 3: P1 → P2A, P2B, PFE (크리티컬)
용도: 고가용성 게이트웨이
```

### 8️⃣ **ring_topology**
```
무엇: 링 네트워크 구성
입력 → 출력:
  - Stream 1: P2A → P2B, P6 (링 입력)
  - Stream 2: P6 → P7, P8 (T1 링)
  - Stream 3: P8 → P1, PFE (백업)
용도: 링 토폴로지
```

### 9️⃣ **load_balancing**
```
무엇: 트래픽 로드 분산
입력 → 출력:
  - Stream 1: P2A → P1, P3, P6, P7 (4개 분산)
  - Stream 2: P2B → PFE, P2A, P8, P9
용도: 부하 분산
```

### 🔟 **mixed_automotive**
```
무엇: 자동차 ECU 네트워크
입력 → 출력:
  - Stream 1: P1 → P6, P7, P8 (진단→ECU)
  - Stream 2: P6 → PFE, P2A (센서 수집)
  - Stream 3: PFE → 모든 외부 포트 (안전 방송)
용도: 자동차 네트워크
```

---

## 💡 사용 예시

### 예시 1: PFE에서 외부로 복제
```bash
# test_scenario 사용
./upload.sh test_scenario

# 트래픽 생성
ping -I pfe0 192.168.1.100

# P2A, P2B에서 동일한 패킷 확인
tcpdump -i [P2A interface]
tcpdump -i [P2B interface]
```

### 예시 2: 최대 복제 테스트
```bash
# maximum_replication 사용
./upload.sh maximum_replication

# PFE에서 전송하면 10개 포트 모두에서 수신
```

### 예시 3: 안전 중요 시스템
```bash
# triple_redundancy 사용
./upload.sh triple_redundancy

# 3개 경로로 동시 전송
```

---

## ❓ FAQ

**Q: 어떤 걸 써야 하나요?**
A: `test_scenario`가 가장 좋습니다.

**Q: P3B는 왜 안 되나요?**
A: P3B는 SJA1110 스위치를 거치지 않고 S32G에 직접 연결됩니다.

**Q: 최대 몇 개 포트로 복제 가능?**
A: 10개 포트 동시 복제 가능 (maximum_replication)

**Q: UC와 Switch 파일 둘 다 필요한가요?**
A: 네, UC는 펌웨어, Switch는 FRER 설정입니다.