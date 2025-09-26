#!/usr/bin/env python3
"""SJA1110 Gold Box firmware packager.

This module builds `sja1110_uc.bin` and `sja1110_switch.bin` images that
follow the expectations of the upstream NXP Linux driver
(`IMAGE_VALID_MARKER`, device ID and CRC32 trailers).  The structural
contents of the files remain intentionally simple – the goal is to provide
valid containers that the driver accepts without tripping header or CRC
checks.  Actual FRER logic must still be provided by the microcontroller
firmware that runs inside the Gold Box.
"""

from __future__ import annotations

import json
import logging
import struct
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

IMAGE_VALID_MARKER = bytes([0x6A, 0xA6] * 4)
DEVICE_ID_SJA1110 = 0xB700030E
CONFIG_FLAGS = (1 << 31) | (1 << 30) | (1 << 29) | (1 << 28)
UC_IMAGE_SIZE = 256 * 1024
SWITCH_IMAGE_SIZE = 640 * 1024


@dataclass
class FRERStream:
    """Description of a FRER replication stream."""

    stream_id: int
    src_port: int
    dst_ports: List[int]
    vlan_id: int = 0
    priority: int = 7
    name: str = ""
    sequence_history: int = 32
    enabled: bool = True


class SJA1110FirmwareBuilder:
    """Light‑weight firmware builder for NXP Gold Box deployments."""

    def __init__(self, host_port: int = 4, cascade_port: int = 10) -> None:
        self.host_port = host_port
        self.cascade_port = cascade_port
        self.streams: List[FRERStream] = []

        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_frer_replication_stream(
        self,
        stream_id: int,
        src_port: int,
        dst_ports: List[int],
        vlan_id: int = 0,
        priority: int = 7,
        name: str = "",
        sequence_history: int = 32,
    ) -> None:
        """Register a replication stream that should appear in the metadata."""

        self.streams.append(
            FRERStream(
                stream_id=stream_id,
                src_port=src_port,
                dst_ports=list(dst_ports),
                vlan_id=vlan_id,
                priority=priority,
                name=name or f"Stream_{stream_id}",
                sequence_history=sequence_history,
            )
        )
        self.logger.info(
            "Configured stream %s: port %d → %s (VLAN %d, prio %d)",
            stream_id,
            src_port,
            dst_ports,
            vlan_id,
            priority,
        )

    def build_microcontroller_firmware(self) -> bytes:
        """Return a minimal UC firmware image with valid header + CRC32."""

        payload = bytearray()
        payload.extend(IMAGE_VALID_MARKER)
        payload.extend(struct.pack("<I", DEVICE_ID_SJA1110))

        # Embed a lightweight manifest describing the configured streams.
        manifest = json.dumps(
            {
                "generated": datetime.now().isoformat(),
                "streams": [
                    {
                        "id": s.stream_id,
                        "src": s.src_port,
                        "dst": s.dst_ports,
                        "vlan": s.vlan_id,
                        "priority": s.priority,
                    }
                    for s in self.streams
                ],
            }
        ).encode("utf-8")

        manifest = manifest[:96]  # keep header compact
        payload.extend(manifest)
        payload.extend(b"\x00" * (96 - len(manifest)))

        # Fill remaining area with 0xFF to match expected size (minus CRC).
        while len(payload) < (UC_IMAGE_SIZE - 4):
            payload.append(0xFF)

        crc = zlib.crc32(payload) & 0xFFFFFFFF
        payload.extend(struct.pack("<I", crc))
        return bytes(payload)

    def build_switch_firmware(self) -> bytes:
        """Create switch configuration container with correct CRC32."""

        config = bytearray()
        config.extend(IMAGE_VALID_MARKER)
        config.extend(struct.pack("<I", DEVICE_ID_SJA1110))
        config.extend(struct.pack("<I", CONFIG_FLAGS))

        # General parameters block at 0x034000 – FRER enable + host/cascade port.
        while len(config) < 0x034000:
            config.append(0x00)

        config.extend(struct.pack("<I", 1))  # FRMREPEN
        config.extend(struct.pack("<BB", self.host_port, self.cascade_port))
        config.extend(b"\x00\x00")  # padding

        # Simplified CB sequence table starting at 0x080000.
        while len(config) < 0x080000:
            config.append(0x00)

        for stream in self.streams:
            entry = bytearray(16)
            port_mask = 0
            for port in stream.dst_ports:
                port_mask |= (1 << port)
            struct.pack_into("<HH", entry, 0, stream.stream_id, port_mask)
            entry[4] = 0x80 if stream.enabled else 0x00
            entry[5] = min(len(stream.dst_ports), 4)  # number of replicas (metadata)
            struct.pack_into("<H", entry, 6, 0)  # sequence number placeholder
            for idx, port in enumerate(stream.dst_ports[:4]):
                entry[8 + idx] = port & 0xFF
            entry[12] = stream.src_port & 0xFF
            entry[13] = stream.priority & 0xFF
            config.extend(entry)

        # CB individual recovery table at 0x090000.
        while len(config) < 0x090000:
            config.append(0x00)

        for stream in self.streams:
            entry = struct.pack(
                "<HBBHHHH",
                stream.stream_id,
                stream.src_port,
                0x80 if stream.enabled else 0x00,
                0,
                stream.sequence_history,
                100,
                len(stream.dst_ports),
            )
            config.extend(entry)

        # DPI table at 0x0A0000.
        while len(config) < 0x0A0000:
            config.append(0x00)

        for stream in self.streams:
            entry = struct.pack(
                "<HHHBBBB",
                stream.stream_id,
                stream.vlan_id & 0x0FFF,
                0xF1C1,
                1 if stream.enabled else 0,
                1,
                stream.priority & 0xFF,
                stream.src_port & 0xFF,
            )
            config.extend(entry)

        # Pad to expected payload size and append CRC.
        while len(config) < SWITCH_IMAGE_SIZE:
            config.append(0xFF)

        crc = zlib.crc32(config) & 0xFFFFFFFF
        config.extend(struct.pack("<I", crc))
        return bytes(config)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def save_configuration_info(
        self, uc_file: str, switch_file: str, output_json: Optional[str] = None
    ) -> None:
        """Persist a manifest describing the generated artefacts."""

        manifest = {
            "generated": datetime.now().isoformat(),
            "uc_firmware": uc_file,
            "switch_config": switch_file,
            "host_port": self.host_port,
            "cascade_port": self.cascade_port,
            "streams": [
                {
                    "stream_id": s.stream_id,
                    "src_port": s.src_port,
                    "dst_ports": s.dst_ports,
                    "vlan": s.vlan_id,
                    "priority": s.priority,
                }
                for s in self.streams
            ],
        }

        path = output_json or "sja1110_firmware_config.json"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2)
        self.logger.info("Saved manifest to %s", path)


def main() -> None:
    builder = SJA1110FirmwareBuilder()

    builder.add_frer_replication_stream(
        stream_id=1,
        src_port=4,
        dst_ports=[2, 3],
        vlan_id=100,
        priority=7,
        name="PFE_to_P2AB",
    )

    builder.add_frer_replication_stream(
        stream_id=2,
        src_port=2,
        dst_ports=[5, 6],
        vlan_id=101,
        priority=6,
        name="P2A_to_T1",
    )

    uc = builder.build_microcontroller_firmware()
    switch = builder.build_switch_firmware()

    with open("sja1110_uc.bin", "wb") as f:
        f.write(uc)
    with open("sja1110_switch.bin", "wb") as f:
        f.write(switch)

    builder.save_configuration_info("sja1110_uc.bin", "sja1110_switch.bin")
    print("Generated sja1110_uc.bin and sja1110_switch.bin")


if __name__ == "__main__":
    main()
