# SJA1110 Firmware Format & Memory Map

본 문서는 **NXP SJA1110 Linux Driver Release v0.4.1** (`sja1110_init.c / sja1110_init.h`)와 Gold Box 실제 바이너리를 분석해 정리한 결과입니다. 저장소 최상위에 포함된 `sja1110-nxp-official/` 디렉터리에서 원본 드라이버 소스를 확인할 수 있습니다.

## 1. 마이크로컨트롤러 펌웨어 (`sja1110_uc*.bin`)

| 오프셋 | 크기 | 설명 |
|--------|------|------|
| `0x000000` | 8 | `IMAGE_VALID_MARKER` (`6A A6` 반복) |
| `0x000008` | 4 | Device ID (`0xB700030E`, little-endian) |
| `0x00000C` | 96 | 메타데이터/헤더 영역 (빌더에서 스트림 정보 기록) |
| `0x00006C` | … | 실행 코드/설정 데이터 (Gold Box용 펌웨어는 여기서 시작) |
| `EOF-4` | 4 | CRC32 (little-endian, payload 전체에 대해 계산) |

> **참고**: 드라이버는 펌웨어 업로드 시 `IMAGE_VALID_MARKER`와 CRC32 만을 엄격히 검사합니다. 그 외의 헤더 구조는 Gold Box uC 구현에 따라 달라질 수 있습니다.

## 2. 스위치 구성 (`sja1110_switch*.bin`)

| 오프셋 | 크기 | 설명 |
|--------|------|------|
| `0x000000` | 8 | `IMAGE_VALID_MARKER` |
| `0x000008` | 4 | Device ID (`0xB700030E`) |
| `0x00000C` | 4 | Configuration Flags (`CF_CONFIGS_MASK`, `CF_CRCCHKL`, `CF_IDS`, `CF_CRCCHKG`) |
| `0x034000` | 4 | `FRMREPEN` (Frame Replication Enable) – 1이면 FRER 활성화 |
| `0x034004` | 1 | Host Port (Gold Box: `0x04` = PFE_MAC0) |
| `0x034005` | 1 | Cascade Port (Gold Box: `0x0A`) |
| `0x040000` | … | VLAN Lookup Table (필요 시 구성) |
| `0x050000` | … | L2 Forwarding Table |
| `0x060000` | … | MAC Configuration Table |
| `0x080000` | 16×N | CB Sequence Generation Table (복제 경로 정의) |
| `0x090000` | 12×N | CB Individual Recovery Table (시퀀스/히스토리) |
| `0x0A0000` | 12×N | DPI Table (스트림 식별, R-TAG, VLAN) |
| `EOF-4` | 4 | CRC32 (little-endian) |

### 2.1 CB Sequence Generation Entry (16 bytes)
```
struct cb_seq_gen {
    uint16_t stream_handle;   // FRER 스트림 ID
    uint16_t port_mask;       // 복제 대상 포트 비트마스크
    uint8_t  flags;           // 0x80 = enable
    uint8_t  replica_count;   // 메타데이터 (빌더 확장 필드)
    uint16_t seq_num;         // 초기 시퀀스 값 (0)
    uint8_t  egress_ports[4]; // 복제 포트 번호 (최대 4개 기록)
    uint8_t  ingress_port;    // 원본 입력 포트
    uint8_t  priority;        // IEEE 802.1Q PCP 값
    uint8_t  reserved[2];
};
```

### 2.2 CB Individual Recovery Entry (12 bytes)
```
struct cb_individual_recovery {
    uint16_t stream_handle;
    uint8_t  ingress_port;
    uint8_t  flags;          // 0x80 = enable
    uint16_t seq_num;        // 초기 시퀀스 (0)
    uint16_t history_len;    // 히스토리 깊이 (예: 32)
    uint16_t reset_timeout;  // 타임아웃 (ms)
    uint16_t replica_count;  // 복제 경로 수 (확장 필드)
};
```

### 2.3 DPI Table Entry (12 bytes)
```
struct dpi_entry {
    uint16_t stream_id;
    uint16_t vlan_id;        // 12-bit VLAN ID
    uint16_t rtag_type;      // 보통 0xF1C1 (IEEE 802.1CB R-TAG)
    uint8_t  cb_enable;      // 0 또는 1
    uint8_t  sn_num_greater; // 항상 1 (시퀀스 비교 방식)
    uint8_t  priority;       // 0~7
    uint8_t  ingress_port;
    uint8_t  reserved[4];
};
```

## 3. CRC32 트레일러
- 모든 바이너리는 **little-endian** CRC32 값을 마지막 4바이트에 포함합니다.
- CRC 계산 시 마지막 4바이트는 제외해야 합니다. (`zlib.crc32(payload[:-4])`)
- `tools/fix_crc.py` 스크립트를 이용하면 바이너리 편집 후 CRC를 자동으로 재계산할 수 있습니다.

## 4. 참고 소스
- `sja1110-nxp-official/sja1110_init.h`
  - `IMAGE_VALID_MARKER`, `CONFIG_START_ADDRESS`, `CF_*` 매크로 정의
- `sja1110-nxp-official/sja1110_init.c`
  - 펌웨어 업로드/검증 루틴 (`sja1110_pre_uc_upload`, `sja1110_simple_upload` 등)
- `docs/goldbox_port_mapping.md`
  - Gold Box 포트 <-> SJA1110 포트 매핑

## 5. Gold Box 기본 포트 매핑 요약
| 포트 | 설명 |
|------|------|
| 1 | P1 (100BASE-TX) |
| 2 | P2A (1000BASE-T) |
| 3 | P2B (1000BASE-T) |
| 4 | PFE_MAC0 (SGMII, CPU) |
| 5 | P6 (100BASE-T1) |
| 6 | P7 (100BASE-T1) |
| 7 | P8 (100BASE-T1) |
| 8 | P9 (100BASE-T1) |
| 9 | P10 (100BASE-T1) |
| 10 | P11 (100BASE-T1) |

P3A, P3B, P5는 SJA1110을 거치지 않고 직접 S32G에 연결되므로 FRER 구성에 포함할 수 없습니다.

---

이 문서는 지속적으로 업데이트 됩니다. 개선 사항이나 공식 문서에 추가로 확인된 정보가 있다면 PR로 공유해 주세요.
