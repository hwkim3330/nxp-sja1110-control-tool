# GitHub Repository Structure

## 📁 전체 디렉토리 구조

```
nxp-sja1110-control-tool/
│
├── 📄 frer                          # ⭐ 메인 FRER 실행 파일 (Python)
├── 📄 README.md                     # 프로젝트 설명서
├── 📄 FRER_CONFIGURATION.md         # FRER 동작 원리 설명
├── 📄 CORRECT_PORT_MAPPING.md       # 올바른 포트 매핑 (P3B 불가능 설명)
├── 📄 BINARY_CATALOG.md             # 바이너리 카탈로그
│
├── 📂 binaries/                     # ⭐ 모든 FRER 바이너리 파일
│   ├── 📄 README.md
│   ├── 📄 upload.sh                 # 업로드 스크립트
│   ├── 📄 sja1110_uc_*.bin          # UC 펌웨어 (각 시나리오별)
│   ├── 📄 sja1110_switch_*.bin      # 스위치 구성 (각 시나리오별)
│   └── 📄 config_*.json             # 구성 정보 JSON
│
├── 📂 my/                           # 원본 바이너리
│   ├── 📄 sja1110_uc.bin
│   ├── 📄 sja1110_switch.bin
│   └── 📄 PFE-FW_S32G_1.11.0.zip
│
├── 📂 src/                          # 소스 코드
│   ├── 📄 sja1110_real_frer.py
│   ├── 📄 sja1110_driver.py
│   ├── 📄 sja1110_firmware_builder.py
│   └── ...
│
├── 📂 docs/                         # 문서
│   ├── 📄 FRER_TEST_PLAN.md
│   └── 📄 goldbox_port_mapping.md
│
├── 📂 config/                       # 구성 파일
│   └── 📄 frer_example.json
│
├── 📂 examples/                     # 예제 스크립트
│   ├── 📄 quick_start_example.py
│   └── 📄 custom_scenario_template.py
│
├── 📂 tests/                        # 테스트 파일
│
├── 📄 generate_all_binaries.py      # 바이너리 생성 스크립트
├── 📄 frer_example.py               # FRER 사용 예제
├── 📄 port_test.sh                  # 포트 테스트 스크립트
├── 📄 goldbox_dual_upload.sh       # 듀얼 업로드 스크립트
├── 📄 goldbox_upload.sh             # 단일 업로드 스크립트
├── 📄 test_frer_goldbox.py          # FRER 테스트 스크립트
│
└── 📄 *.bin                         # 기타 바이너리 파일들
```

## 🎯 주요 파일 설명

### 1. **frer** (메인 실행 파일)
```bash
# 사용법
./frer test                          # 테스트 실행
./frer scenario --scenario basic_rj45 # 시나리오 로드
./frer add-stream --stream-id 1 --src-port 4 --dst-ports 2 3
```

### 2. **binaries/** 디렉토리
10가지 시나리오별 바이너리:
- `basic_rj45` - 기본 RJ45 복제
- `test_scenario` - 종합 테스트
- `maximum_replication` - 최대 복제 (1→10 포트)
- `triple_redundancy` - 3중 이중화
- `rj45_to_automotive` - RJ45→T1 브리지
- 등등...

### 3. **포트 매핑 (중요!)**
```
Port 4: PFE_MAC0 (입력) → Port 2,3: P2A,P2B (출력)
```
- ❌ P3B는 사용 불가 (SJA1110 거치지 않음)
- ✅ Port 4 (PFE_MAC0)가 호스트 포트

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/hwkim3330/nxp-sja1110-control-tool.git
cd nxp-sja1110-control-tool
```

### 2. FRER 테스트
```bash
# 테스트 시나리오 실행
./frer test

# 바이너리 업로드
cd binaries
./upload.sh test_scenario
```

### 3. 커스텀 구성
```bash
# PFE → P2A, P2B 복제
./frer add-stream --stream-id 1 --src-port 4 --dst-ports 2 3
./frer generate-binary --output my_config.bin
```

## 📊 바이너리 구조

```
Offset      | Content                 | Size
------------|-------------------------|----------
0x000000    | IMAGE_VALID_MARKER      | 8 bytes
0x000008    | DEVICE_ID (0xb700030e)  | 4 bytes
0x034000    | FRMREPEN=1              | 4 bytes
0x034004    | Host Port=4             | 1 byte
0x080000    | CB Seq Gen Table        | Variable
0x090000    | CB Ind Recovery Table   | Variable
0x0A0000    | DPI Table               | Variable
End-4       | CRC32                   | 4 bytes
```

## 🔗 GitHub 링크

**Repository:** https://github.com/hwkim3330/nxp-sja1110-control-tool

## 📝 파일 크기

- **UC 바이너리:** 320,280 bytes
- **Switch 바이너리:** 655,360+ bytes
- **총 바이너리 파일:** 50+ 개

## ⚠️ 중요 사항

1. **P3B 사용 불가** - S32G에 직접 연결
2. **Port 4가 호스트** - PFE_MAC0
3. **Port 2,3이 출력** - P2A, P2B
4. **Root 권한 필요** - sudo 사용

## 📞 문의

GitHub Issues: https://github.com/hwkim3330/nxp-sja1110-control-tool/issues