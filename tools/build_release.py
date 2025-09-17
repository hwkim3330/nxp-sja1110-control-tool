#!/usr/bin/env python3
import os
import json
from datetime import datetime
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
sys.path.append(os.path.join(ROOT, 'src'))

from sja1110_dual_firmware import SJA1110FirmwareBuilder  # type: ignore


def build_scenario(name, streams, out_dir, vlan_id=None):
    b = SJA1110FirmwareBuilder()
    for s in streams:
        vid = s.get('vlan_id', vlan_id if vlan_id is not None else 100)
        b.add_frer_replication_stream(
            stream_id=s['id'],
            src_port=s['src'],
            dst_ports=s['dst'],
            vlan_id=vid,
            priority=s.get('prio', 7),
            name=s.get('name', name)
        )
    uc = b.build_microcontroller_firmware()
    sw = b.build_switch_firmware()
    uc_file = os.path.join(out_dir, f"sja1110_uc_{name}.bin")
    sw_file = os.path.join(out_dir, f"sja1110_switch_{name}.bin")
    with open(uc_file, 'wb') as f:
        f.write(uc)
    with open(sw_file, 'wb') as f:
        f.write(sw)
    # Save manifest
    meta = {
        'name': name,
        'files': {'uc': os.path.basename(uc_file), 'switch': os.path.basename(sw_file)},
        'streams': streams,
        'vlan': vlan_id,
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

    manifest = {'release': stamp, 'scenarios': []}

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

