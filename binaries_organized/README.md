# 정리된 바이너리 폴더

## 📁 폴더 구조 (이름만 보고 선택!)

```
01_test_scenario_RECOMMENDED/    ⭐ 추천! PFE→P2A,P2B 복제
02_basic_rj45_simple/            기본 P1→P2A,P2B
03_maximum_10ports/              1→10포트 최대 복제
04_triple_redundancy_safety/     3중 안전 복제
05_dual_path/                    2중 경로
06_rj45_to_t1_bridge/           RJ45→T1 변환
07_redundant_gateway/            이중화 게이트웨이
08_ring_topology/                링 네트워크
09_load_balancing/               부하 분산
10_automotive_ecu/               자동차 ECU
```

## 🚀 사용법

### 1. 원하는 폴더 선택
```bash
cd 01_test_scenario_RECOMMENDED
```

### 2. 업로드
```bash
./upload.sh
```

## 📊 각 폴더 내용

모든 폴더에 동일한 파일명:
- `sja1110_uc.bin` - UC 펌웨어
- `sja1110_switch.bin` - Switch 구성
- `upload.sh` - 업로드 스크립트

## ⭐ 추천

**`01_test_scenario_RECOMMENDED`** 사용!
- PFE (Port 4) → P2A, P2B (Port 2,3) 복제
- 가장 완벽한 테스트 구성