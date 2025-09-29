# NXP SJA1110 Gold Box FRER – Validated Release

This release provides known‑good FRER binaries and simple tooling for the Gold Box.

## What’s Included
- `binaries_release/latest`
  - `sja1110_uc.bin` / `sja1110_switch.bin` (P4→P2A,P2B, untagged)
  - `index.json` describing recommended + alternative scenarios
- `binaries_release/2025-09-29-multi`
  - p4→p2ab, p4→p6p7, p2a→p4,p2b (각 tagged/untagged 구성)
  - `manifest.json` (생성 메타데이터)
- `tools`
  - `apply_frer.sh` – sysfs 업로드 (switch → uC 순서 자동)
  - `build_release.py` – 검증된 시나리오 재생성
  - `fix_crc.py` – 바이너리 수정 후 CRC32 트레일러 재계산

## Quick Start (Untagged Recommended)
```
cd binaries_release/latest
sudo ../../tools/apply_frer.sh sja1110_uc.bin sja1110_switch.bin
```

Then send traffic from PFE (pfe0) and observe replication on sw0p2 and sw0p3.

## Notes
- Mapping is verified: Port 4 = PFE_MAC0 (CPU). P3A/P3B/P5 are not behind SJA1110.
- Gold Box performs replication only; elimination is at the receiver.
- For VLAN scenarios, use the non‑“untag” binaries.

## Housekeeping
- Legacy/uncertain binaries were moved to `archive/` to avoid confusion. If you prefer, they can be deleted entirely in a follow‑up.
