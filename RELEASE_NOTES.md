# NXP SJA1110 Gold Box FRER – Validated Release

This release provides known‑good FRER binaries and simple tooling for the Gold Box.

## What’s Included
- binaries_release/2025-09-16-p4-to-p2ab
  - sja1110_uc.bin / sja1110_switch.bin (P4→P2A,P2B, VLAN 100)
  - sja1110_uc_p4_to_p2ab_untag.bin / sja1110_switch_p4_to_p2ab_untag.bin (untagged)
- binaries_release/2025-09-17-multi
  - p4→p2ab, p4→p6p7, p2a→p4,p2b (each tagged/untagged)
  - manifest.json (contents overview)
- tools
  - apply_frer.sh – sysfs upload (detects endpoints; switch→uC order)
  - build_release.py – regenerates validated scenarios

## Quick Start (Untagged Recommended)
```
cd binaries_release/2025-09-16-p4-to-p2ab
sudo ../../tools/apply_frer.sh sja1110_uc_p4_to_p2ab_untag.bin sja1110_switch_p4_to_p2ab_untag.bin
```

Then send traffic from PFE (pfe0) and observe replication on sw0p2 and sw0p3.

## Notes
- Mapping is verified: Port 4 = PFE_MAC0 (CPU). P3A/P3B/P5 are not behind SJA1110.
- Gold Box performs replication only; elimination is at the receiver.
- For VLAN scenarios, use the non‑“untag” binaries.

## Housekeeping
- Legacy/uncertain binaries were moved to `archive/` to avoid confusion. If you prefer, they can be deleted entirely in a follow‑up.
