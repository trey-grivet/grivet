# Zebra StageNow – Port 8080 Fix & Network Troubleshooting Checklist

Companion to *Zebra StageNow Warehouse Full Provisioning – Non-Xpert Production Guide*.
Server: `192.168.0.91` · Port: `8080` (guide was written for `8081`).

> StageNow admin password is intentionally **not** stored here. Keep it in the company password manager.

## 1. Root-cause candidates (ranked)

| # | Likely cause | Likelihood | Quick test |
|---|---|---|---|
| 1 | Port mismatch: guide binds IIS + firewall + every URL to **8081**; server opened **8080** | ~45% | `netstat -ano \| findstr :808` on server — which port is IIS listening on? |
| 2 | Expecting a network "push" — StageNow is **scan-to-pull** only (no MDM) | ~20% | Each TC22 must scan the barcodes; devices then download from IIS |
| 3 | Old barcodes still point to old URL/port/FTP | ~15% | Barcodes regenerated after last URL change? |
| 4 | TC22s can't reach 192.168.0.91 (different VLAN/subnet, guest SSID, client isolation) | ~10% | Browse `http://192.168.0.91:8080/test.txt` in a browser **on a TC22** |
| 5 | Windows network profile = Public, firewall rule only on Domain/Private; or server IP not reserved | ~10% | `Get-NetConnectionProfile` / DHCP reservation for .91 |

## 2. Make everything say 8080 (all four places must match)

1. **IIS binding** – IIS Manager → Sites → ZebraDeployment → Bindings → http, IP `192.168.0.91`, port **8080**.
2. **Windows Firewall** – inbound TCP **8080**, Allow, profiles Domain + Private (+ Public if the NIC shows Public), scope 192.168.0.0/24.
3. **StageNow APK source URLs** (steps 14–15):
   - `http://192.168.0.91:8080/APKs/Current/grivet_scan_assist.apk`
   - `http://192.168.0.91:8080/APKs/Current/skustack.apk`
4. **StageNow deployment package URL** (step 38):
   - `http://192.168.0.91:8080/Profiles/Warehouse-Full-Provisioning/JsWarehouse-Full-Provisioning_ExecuteSection.bin`

Then **re-publish → regenerate JS PDF417 barcodes → discard all old printed barcodes.**

Note: changing APK URLs means reopening the Deployment section only. Do **not** reopen the network (Wi-Fi) branch — the guide warns that broke the profile previously.

## 3. Verify before scanning (gate)

Run on the server (PowerShell, admin):

```powershell
netstat -ano | findstr :8080                       # IIS (PID 4 / System) must be LISTENING
Get-NetConnectionProfile                           # NetworkCategory should be Private/Domain
Get-NetFirewallRule -DisplayName "*8080*" | Get-NetFirewallPortFilter
Invoke-WebRequest http://192.168.0.91:8080/test.txt -UseBasicParsing
```

Then from a **TC22 browser on the warehouse SSID** (not the server, not a laptop on a different network):

- [ ] `http://192.168.0.91:8080/test.txt` → "Zebra deployment server working"
- [ ] `.../APKs/Current/grivet_scan_assist.apk` downloads
- [ ] `.../APKs/Current/skustack.apk` downloads
- [ ] `.../Profiles/Warehouse-Full-Provisioning/JsWarehouse-Full-Provisioning_ExecuteSection.bin` downloads

Error map: timeout = firewall/VLAN/binding · 404 = path/filename · 404.3 = missing MIME type · 403 = request filtering/permissions.

## 4. Other checks

- [ ] Server `192.168.0.91` is static or DHCP-reserved (if it changes, every barcode breaks).
- [ ] Warehouse SSID hands out 192.168.0.x addresses and has client isolation **off**.
- [ ] Nothing else (Tomcat, Jenkins, proxies) already owns 8080.
- [ ] Device MX version ≥ 13.3 (StageNow client → About). TC21s validated separately.
- [ ] Pilot on one TC22, run the step-40 checklist, then roll out.

## 5. If true remote push is the goal

StageNow cannot push to devices. Options: Zebra/SOTI MobiControl, 42Gears SureMDM, Microsoft Intune, or Zebra-supported EMMs — typically ~$3–6/device/month. Decide before scaling past ~20 devices or when frequent APK updates are expected.
