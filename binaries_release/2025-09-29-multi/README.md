# 2025-09-29 FRER Multi-Scenario Release

Validated FRER binaries generated from the official NXP base configuration.

## Contents
- `sja1110_uc_p4_to_p2ab[_untag].bin` (골드박스 UC 펌웨어 원본) + `sja1110_switch_p4_to_p2ab[_untag].bin`
- `sja1110_uc_p4_to_t1_p6p7[_untag].bin` + matching switch binaries
- `sja1110_uc_p2a_to_p4_p2b[_untag].bin` + matching switch binaries
- `manifest.json` (`schema_version=1`, CRC/size metadata)

## 기본 UC 펌웨어
모든 `sja1110_uc_*.bin` 파일은 `/home/kim/s32g2/sja1110_uc.bin`에서 추출한 골드박스 공식 펌웨어를 그대로 사용합니다. CRC32는 전체 파일에 대해 계산해 메타데이터에 기록했습니다.

## Usage
```bash
sudo ../../tools/apply_frer.sh sja1110_uc_p4_to_p2ab_untag.bin sja1110_switch_p4_to_p2ab_untag.bin
```

- VLAN 100 변형을 원하면 `_p4_to_p2ab.bin`을 사용하세요.
- Port 4 → T1 포트(P6/P7) 또는 Port 2 → Port 4/3 시나리오도 동일한 방식으로 업로드할 수 있습니다.

모든 스위치 바이너리는 `config/base_switch_words.json`에 저장된 NXP 기본 레지스터 값 위에 FRER 테이블을 덧씌운 뒤 CRC32를 재계산합니다. 자세한 메모리 레이아웃과 필드 설명은 `../../docs/SJA1110_Firmware_Format.md`를 참고해 주세요.
