# 바이너리 파일 정리

## 📂 /binaries/ 폴더 (메인 - 이거 쓰면 됨!)

### UC 바이너리 (마이크로컨트롤러)
```
sja1110_uc_basic_rj45.bin          - 기본 테스트용
sja1110_uc_test_scenario.bin       - 종합 테스트용 ⭐
sja1110_uc_dual_path.bin           - 2개 경로 복제
sja1110_uc_triple_redundancy.bin   - 3개 경로 복제
sja1110_uc_maximum_replication.bin - 최대 복제 (10포트)
sja1110_uc_rj45_to_automotive.bin  - RJ45→T1 변환
sja1110_uc_ring_topology.bin       - 링 네트워크
sja1110_uc_redundant_gateway.bin   - 이중화 게이트웨이
sja1110_uc_load_balancing.bin      - 로드 분산
sja1110_uc_mixed_automotive.bin    - 자동차 네트워크
sja1110_uc_master.bin               - 마스터 (모든 스위치와 호환)
```

### Switch 바이너리 (FRER 설정)
```
sja1110_switch_basic_rj45.bin          - P1 → P2A,P2B 복제
sja1110_switch_test_scenario.bin       - PFE → P2A,P2B 복제 ⭐
sja1110_switch_dual_path.bin           - 2개 경로
sja1110_switch_triple_redundancy.bin   - 3개 경로
sja1110_switch_maximum_replication.bin - 1→10 포트 복제
sja1110_switch_rj45_to_automotive.bin  - RJ45→T1 4개 복제
sja1110_switch_ring_topology.bin       - 링 구성
sja1110_switch_redundant_gateway.bin   - 백업 경로 포함
sja1110_switch_load_balancing.bin      - 4포트 분산
sja1110_switch_mixed_automotive.bin    - ECU 네트워크
```

### 사용법
```bash
cd binaries
./upload.sh test_scenario  # 가장 추천!
```

---

## 📂 루트 폴더 (/)

### 현재 사용 중인 바이너리
```
sja1110_uc.bin        - 현재 UC (test_scenario)
sja1110_switch.bin    - 현재 Switch (test_scenario)
```

### 테스트 바이너리
```
frer_test.bin         - FRER 테스트용
goldbox_frer.bin      - Gold Box FRER 구성
```

### 이전 버전들
```
sja1110_frer.bin
sja1110_goldbox.bin
sja1110_switch_corrected.bin
sja1110_uc_corrected.bin
```

---

## 📂 /my/ 폴더

### 원본 파일 (참고용)
```
sja1110_uc.bin        - 원본 UC
sja1110_switch.bin    - 원본 Switch
PFE-FW_S32G_1.11.0.zip - PFE 펌웨어
```

---

## 🎯 뭘 써야 하나?

### 1. 가장 간단한 테스트
```bash
cd binaries
./upload.sh test_scenario
```
이게 제일 좋음. PFE(Port 4) → P2A,P2B(Port 2,3) 복제

### 2. 최대 복제 테스트
```bash
./upload.sh maximum_replication
```
1개 입력 → 10개 포트로 복제

### 3. 3중 이중화 (안전 critical)
```bash
./upload.sh triple_redundancy
```
중요한 데이터 3중 복제

---

## ⚠️ 중요!

### 포트 번호
- Port 4 = PFE (CPU 연결)
- Port 2 = P2A (1G RJ45)
- Port 3 = P2B (1G RJ45)
- Port 1 = P1 (100M RJ45)
- Port 5-10 = P6-P11 (T1)

### P3B는 왜 안되나?
P3B는 SJA1110 스위치를 거치지 않고 S32G에 직접 연결되어 있어서 FRER 불가능

### 복제 경로
```
PFE (Port 4) → P2A (Port 2), P2B (Port 3)
```

---

## 📥 다운로드

GitHub: https://github.com/hwkim3330/nxp-sja1110-control-tool

```bash
git clone https://github.com/hwkim3330/nxp-sja1110-control-tool.git
cd nxp-sja1110-control-tool/binaries
ls *.bin
```