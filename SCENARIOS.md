## FRER Scenarios (Validated)

Use `binaries_release/latest` for the recommended pair. Additional validated variants are in `binaries_release/2025-09-17-multi`.

- Recommended (untagged):
  - Name: p4_to_p2ab_untag
  - Ingress: P4 (PFE_MAC0)
  - Egress: P2A, P2B
  - Files: `binaries_release/latest/sja1110_uc.bin`, `binaries_release/latest/sja1110_switch.bin`

- Alternatives:
  - p4_to_p2ab (VLAN 100): `binaries_release/2025-09-17-multi/sja1110_uc_p4_to_p2ab.bin`, `.../sja1110_switch_p4_to_p2ab.bin`
  - p4_to_t1_p6p7_untag (VLAN 0): `.../sja1110_uc_p4_to_t1_p6p7_untag.bin`, `.../sja1110_switch_p4_to_t1_p6p7_untag.bin`
  - p2a_to_p4_p2b_untag (VLAN 0): `.../sja1110_uc_p2a_to_p4_p2b_untag.bin`, `.../sja1110_switch_p2a_to_p4_p2b_untag.bin`

Apply helper:
```
sudo tools/apply_frer.sh <UC_BIN> <SWITCH_BIN>
```
