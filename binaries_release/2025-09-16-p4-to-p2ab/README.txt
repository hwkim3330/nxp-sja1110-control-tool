Gold Box FRER Release (2025-09-16)

Content
- sja1110_uc.bin: Default UC firmware (P4->P2A,P2B, VLAN 100)
- sja1110_switch.bin: Default switch config (P4->P2A,P2B, VLAN 100)
- sja1110_uc_p4_to_p2ab.bin: UC firmware (same as default)
- sja1110_switch_p4_to_p2ab.bin: Switch config (same as default)
- sja1110_uc_p4_to_p2ab_untag.bin: UC firmware (VLAN 0 untagged)
- sja1110_switch_p4_to_p2ab_untag.bin: Switch config (VLAN 0 untagged)

Usage (sysfs upload order matters: switch then UC)
1) Copy files to /lib/firmware
2) Upload switch config, then UC firmware:
   echo sja1110_switch.bin > /sys/bus/spi/devices/spi0.0/switch-configuration/switch_cfg_upload
   echo sja1110_uc.bin > /sys/bus/spi/devices/spi0.1/uc-configuration/uc_fw_upload
3) Optionally reset:
   echo 1 > /sys/bus/spi/devices/spi0.0/switch-configuration/switch_reset

Test
- Send traffic from PFE (pfe0) and observe replication on sw0p2, sw0p3.

Notes
- Gold Box performs replication only; elimination at receiver.
