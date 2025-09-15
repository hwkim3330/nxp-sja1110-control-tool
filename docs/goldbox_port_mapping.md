# NXP Gold Box (S32G-VNP-GLDBOX) Port Mapping

## Physical Connectors to SJA1110 Mapping

### External Connectors (User Accessible)
```
Physical Port | Connector Type | Speed      | SJA1110 Port | PHY/Connection
--------------|----------------|------------|--------------|----------------
P1            | RJ45          | 100BASE-TX | Port 1       | Direct
P2A           | RJ45          | 1000BASE-T | Port 2       | AR8035 PHY (RGMII)
P2B           | RJ45          | 1000BASE-T | Port 3       | AR8035 PHY (RGMII)
P3A           | RJ45          | 1000BASE-T | GMAC0        | KSZ9031 PHY (S32G direct)
P3B           | RJ45          | 1000BASE-T | PFE_MAC2     | KSZ9031 PHY (S32G direct)
P4            | RJ45          | 100BASE-TX | Port 1       | SJA1110A
P5            | RJ45          | 1000BASE-T | PFE_MAC1     | S32G direct
P6-P11        | Mini50        | 100BASE-T1 | Port 5-10    | TJA1101 PHYs
```

### Internal Connections (S32G ↔ SJA1110)
```
S32G Interface | Connection Type | SJA1110 Port | Description
---------------|-----------------|--------------|-------------
PFE_MAC0       | SGMII          | Port 4       | Packet Forwarding Engine
PFE_MAC1       | External       | -            | Direct to P5 connector
PFE_MAC2       | External       | -            | Direct to P3B connector
GMAC0          | External       | -            | Direct to P3A connector
```

## SJA1110 Internal Port Assignment

```
Port 0: Reserved/Internal
Port 1: 100BASE-TX (P1/P4 external)
Port 2: 1000BASE-T via AR8035 RGMII (P2A external)
Port 3: 1000BASE-T via AR8035 RGMII (P2B external)
Port 4: SGMII to S32G PFE_MAC0 (internal)
Port 5: 100BASE-T1 (P6 external)
Port 6: 100BASE-T1 (P7 external)
Port 7: 100BASE-T1 (P8 external)
Port 8: 100BASE-T1 (P9 external)
Port 9: 100BASE-T1 (P10 external)
Port 10: 100BASE-T1 (P11 external)
```

## FRER Configuration Planning

### Test Scenario 1: PFE to External Redundancy
- **Input**: PFE_MAC0 (SJA1110 Port 4)
- **Primary Path**: Port 4 → Port 2 → P2A
- **Secondary Path**: Port 4 → Port 3 → P2B
- **Elimination**: At receiving device connected to P2A/P2B

### Test Scenario 2: External to PFE Redundancy
- **Input**: P2A (SJA1110 Port 2)
- **Replication**: Port 2 → Port 5, 6 (100BASE-T1)
- **Elimination**: Port 4 (back to PFE_MAC0)

### Test Scenario 3: 100BASE-T1 Ring Redundancy
- **Input**: P6 (SJA1110 Port 5)
- **Primary Path**: Port 5 → Port 7 → P8
- **Secondary Path**: Port 5 → Port 8 → P9
- **Elimination**: Port 9 or 10

## Important Notes

1. **PFE (Packet Forwarding Engine)**: S32G's hardware accelerated packet processor
2. **GMAC**: Gigabit MAC controller in S32G
3. **AR8035**: Atheros Gigabit PHY for RGMII to 1000BASE-T conversion
4. **KSZ9031**: Micrel Gigabit PHY
5. **TJA1101**: NXP 100BASE-T1 automotive Ethernet PHY

## Switch Configuration Considerations

- Port 4 (SGMII to PFE) is typically the host port
- Ports 2-3 (RGMII) handle high-speed external traffic
- Ports 5-10 (100BASE-T1) for automotive/industrial applications
- FRER should be configured considering actual traffic patterns