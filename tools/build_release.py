#!/usr/bin/env python3
import os
import json
import zlib
from pathlib import Path
from datetime import datetime
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
sys.path.append(os.path.join(ROOT, 'src'))
BASE_SWITCH_JSON = Path(ROOT) / 'config' / 'base_switch_words.json'
BASE_UC_PATH = Path(ROOT) / 'config' / 'base_uc.bin'

from sja1110_dual_firmware import SJA1110FirmwareBuilder  # type: ignore


def load_base_switch_words():
    if BASE_SWITCH_JSON.exists():
        with open(BASE_SWITCH_JSON, 'r') as f:
            data = json.load(f)
        return data.get('words', [])
    return []


BASE_SWITCH_WORDS = load_base_switch_words()


def load_base_uc() -> bytes:
    if BASE_UC_PATH.exists():
        return BASE_UC_PATH.read_bytes()
    raise FileNotFoundError(f"Missing base UC firmware: {BASE_UC_PATH}")


BASE_UC_DATA = load_base_uc()


def overlay_base_switch(payload: bytearray) -> None:
    if not BASE_SWITCH_WORDS:
        return
    for idx, word in enumerate(BASE_SWITCH_WORDS):
        offset = idx * 4
        if offset + 4 > len(payload):
            break
        payload[offset:offset + 4] = word.to_bytes(4, 'little')


def build_scenario(name, streams, out_dir, vlan_id=None, host_port=4, cascade_port=10):
    builder = SJA1110FirmwareBuilder(host_port=host_port, cascade_port=cascade_port)
    for s in streams:
        vid = s.get('vlan_id', vlan_id if vlan_id is not None else 100)
        builder.add_frer_replication_stream(
            stream_id=s['id'],
            src_port=s['src'],
            dst_ports=s['dst'],
            vlan_id=vid,
            priority=s.get('prio', 7),
            name=s.get('name', name)
        )
    sw = bytearray(builder.build_switch_firmware())
    overlay_base_switch(sw)
    payload = sw[:-4]
    crc_sw = zlib.crc32(payload) & 0xFFFFFFFF
    sw[-4:] = crc_sw.to_bytes(4, 'little')
    uc_file = os.path.join(out_dir, f"sja1110_uc_{name}.bin")
    sw_file = os.path.join(out_dir, f"sja1110_switch_{name}.bin")
    with open(uc_file, 'wb') as f:
        f.write(BASE_UC_DATA)
    with open(sw_file, 'wb') as f:
        f.write(sw)
    uc_meta = {
        'path': os.path.basename(uc_file),
        'size': len(BASE_UC_DATA),
        'crc32': f"0x{zlib.crc32(BASE_UC_DATA) & 0xFFFFFFFF:08x}"
    }
    sw_meta = {
        'path': os.path.basename(sw_file),
        'size': len(sw),
        'crc32': f"0x{crc_sw:08x}"
    }
    meta = {
        'name': name,
        'files': {'uc': uc_meta, 'switch': sw_meta},
        'streams': streams,
        'vlan': vlan_id if vlan_id is not None else 100,
        'generated': datetime.now().isoformat()
    }
    return meta


def main():
    # Validated scenarios focusing on reliable ports (P4, P2A, P2B, P6/P7)
    scenarios = [
        {
            'name': 'p4_to_p2ab',
            'streams': [
                {'id': 1, 'src': 4, 'dst': [2, 3], 'name': 'PFE_to_P2AB'}
            ]
        },
        {
            'name': 'p4_to_t1_p6p7',
            'streams': [
                {'id': 2, 'src': 4, 'dst': [5, 6], 'name': 'PFE_to_T1_P6P7'}
            ]
        },
        {
            'name': 'p2a_to_p4_p2b',
            'streams': [
                {'id': 3, 'src': 2, 'dst': [4, 3], 'name': 'P2A_to_PFE_P2B'}
            ]
        }
    ]

    stamp = datetime.now().strftime('%Y-%m-%d-multi')
    out_dir = os.path.join(ROOT, 'binaries_release', stamp)
    os.makedirs(out_dir, exist_ok=True)

    manifest = {
        'schema_version': 1,
        'release': stamp,
        'device': 'SJA1110',
        'host_port': 4,
        'cascade_port': 10,
        'scenarios': []
    }

    for sc in scenarios:
        # Tagged (VLAN 100) and untagged (VLAN 0)
        meta_tag = build_scenario(sc['name'], sc['streams'], out_dir, vlan_id=100)
        meta_untag = build_scenario(sc['name'] + '_untag', sc['streams'], out_dir, vlan_id=0)
        manifest['scenarios'].append(meta_tag)
        manifest['scenarios'].append(meta_untag)

    with open(os.path.join(out_dir, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"Release generated at: {out_dir}")


if __name__ == '__main__':
    main()
