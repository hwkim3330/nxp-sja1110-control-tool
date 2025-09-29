# 2025-09-29 FRER Multi-Scenario Release

Validated FRER binaries generated with the CRC-safe builder.

## Contents
- `sja1110_uc_p4_to_p2ab[_untag].bin` + `sja1110_switch_p4_to_p2ab[_untag].bin`
- `sja1110_uc_p4_to_t1_p6p7[_untag].bin` + matching switch binaries
- `sja1110_uc_p2a_to_p4_p2b[_untag].bin` + matching switch binaries
- `manifest.json` (schema_version=1, CRC/size metadata)

## Usage
```bash
sudo ../../tools/apply_frer.sh sja1110_uc_p4_to_p2ab_untag.bin sja1110_switch_p4_to_p2ab_untag.bin
```

Use the tagged variants when VLAN segregation is required (VLAN 100). All binaries overlay the official base configuration (`config/base_switch_words.json`) and include verified IMAGE_VALID_MARKER headers plus little-endian CRC32 trailers. 자세한 포맷은 `../../docs/SJA1110_Firmware_Format.md`에서 확인하세요.
