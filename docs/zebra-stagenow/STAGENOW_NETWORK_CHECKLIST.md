# Zebra StageNow – Network & Wireless Troubleshooting Checklist

Companion to *Zebra StageNow Warehouse Full Provisioning – Non-Xpert Production Guide*.
Server: `192.168.0.91` (fixed by DHCP reservation) · Port: **8081 per guide** (confirm; 8080 also possible).
Scanners: dedicated VLAN + dedicated 5 GHz-only SSID, WPA2-Personal.

> StageNow admin password is intentionally **not** stored here. Keep it in the company password manager.

## 1. Root-cause candidates (ranked)

| # | Likely cause | Likelihood | Quick test |
|---|---|---|---|
| 1 | Scanner VLAN can't reach 192.168.0.91 (no inter-VLAN rule, or Windows Firewall rule scoped to 192.168.0.0/24 / "Local subnet") | ~35% | TC22 browser → `http://192.168.0.91:8081/test.txt` |
| 2 | Port mismatch somewhere (IIS binding, firewall, APK URLs, .bin URL not all identical) | ~20% | `netstat -ano \| findstr :808` on server |
| 3 | Expecting a network "push" — StageNow is **scan-to-pull** only (no MDM) | ~15% | Each device must scan the barcodes |
| 4 | TC22 can't join 5 GHz SSID (DFS channel, no 802.11d country code, WPA3-only, hidden SSID) | ~10% | Does the TC22 join the SSID manually before staging? |
| 5 | MAC allowlisting on the VLAN while TC22 uses a randomized MAC | ~10% | Router client list: MAC shown vs. MAC on device label |
| 6 | Old barcodes still point to old URL/port | ~10% | Barcodes regenerated after last change? |

## 2. Network path (scanner VLAN → server)

1. **Router/firewall inter-VLAN rule:** allow *scanner VLAN subnet → 192.168.0.91, TCP 8081*. Only that port — do not open the whole LAN to the scanner VLAN.
2. **Windows Firewall rule (8081 inbound):** Remote IP scope must include the **scanner VLAN subnet**. "Local subnet" or 192.168.0.0/24 alone will block it.
3. **No WAN port forward.** Devices are internal; if 8081 was forwarded from the internet on the router, delete that rule.
4. Scanner VLAN needs DHCP + DNS + internet egress (for SkuStack / other cloud apps).

## 3. Make the port identical in all four places

1. IIS binding — Sites → ZebraDeployment → Bindings → `192.168.0.91 : 8081`
2. Windows Firewall inbound TCP rule
3. StageNow APK source URLs (steps 14–15): `http://192.168.0.91:8081/APKs/Current/grivet_scan_assist.apk`, `.../skustack.apk`
4. StageNow deployment package URL (step 38): `http://192.168.0.91:8081/Profiles/Warehouse-Full-Provisioning/JsWarehouse-Full-Provisioning_ExecuteSection.bin`

Then re-publish → regenerate JS PDF417 barcodes → destroy old ones.

## 4. Wireless (5 GHz-only SSID) – AP-side requirements

Guide's StageNow Wi-Fi values (steps 9–12) are correct for WPA2-Personal. The AP must match:

- [ ] Security **WPA2-Personal, AES/CCMP** (WPA2/WPA3 transition OK; **not WPA3-only**, not TKIP).
- [ ] SSID **broadcast** (not hidden); name/passphrase typed exactly (case-sensitive).
- [ ] **Non-DFS channels** (36–48, 149–165). DFS channels cause slow scans/connects and roaming drops on handhelds.
- [ ] **802.11d / country code (US)** advertised by the AP, so the TC22 doesn't fall back to restricted world-mode channels.
- [ ] 20 or 40 MHz channel width (avoid 80/160 MHz in dense racking).
- [ ] **Coverage walk**: 5 GHz loses more through steel racking/inventory. Target ≥ –67 dBm at the far aisles, test in the back corners, freezer/dock areas.
- [ ] Client isolation irrelevant for server on wired LAN, but must not block VLAN routing.

## 5. Fixed MAC address – gap in the current profile

- TC22 (Android 13+) uses a **randomized MAC per SSID** by default. The non-Xpert guide intentionally does **not** change this (see guide p. 5 and p. 13).
- Randomized MAC is usually stable for that SSID but **changes after Enterprise/Factory reset** or if the network profile is deleted and re-added.
- **If the VLAN uses MAC allowlisting/filtering:** the device's first connection uses the random MAC → blocked → can't download the profile. Staging fails.
- **Fix:** add the Xpert-mode **Wi-Fi CSP → MAC Randomization: Disable (use device MAC)** that the guide says was already proven. It must apply in the **staging (Wi-Fi) barcode section**, before/with the network add, or use a separate profile scanned first.
- Retest MDNA licensing on that Wi-Fi CSP setting on one TC22 before rollout.

## 6. Verify before scanning (gate)

Server (PowerShell, admin):

```powershell
netstat -ano | findstr :8081
Get-NetConnectionProfile
Get-NetFirewallRule -DisplayName "*8081*" | Get-NetFirewallAddressFilter   # RemoteAddress must include scanner VLAN
Invoke-WebRequest http://192.168.0.91:8081/test.txt -UseBasicParsing
```

From a **TC22 on the scanner SSID**:

- [ ] `http://192.168.0.91:8081/test.txt`
- [ ] both APK URLs download
- [ ] `.bin` URL downloads

Error map: timeout = VLAN rule / Windows Firewall scope / binding · 404 = path/filename · 404.3 = MIME type · 403 = request filtering/permissions.

## 7. Other plan risks

- **Wi-Fi settings locked (step 22):** if the SSID passphrase ever changes, every device must be re-staged with a new barcode. Keep a "Wi-Fi change" profile ready.
- **Printed barcodes contain the Wi-Fi passphrase** (encrypted, but any Zebra device can use them). Store securely; shred superseded sets.
- **Play Store blocked:** app updates only via re-staging (or MDM). Replacement APKs must keep the same signing key and filename.
- **First launch permissions:** Grivet Scan Assist / SkuStack will prompt on first launch (no MDM to pre-grant). Include in pilot.
- **MX version:** device MX must be ≥ 13.3. Validate TC21s separately.

## 8. If true remote push is the goal

StageNow cannot push. Options: SOTI MobiControl, 42Gears SureMDM, Microsoft Intune, other Zebra-validated EMMs — roughly $3–6/device/month (estimate; get quotes).
