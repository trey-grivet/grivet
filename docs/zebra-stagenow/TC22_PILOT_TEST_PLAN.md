# TC22 Pilot Test Plan – Warehouse-Full-Provisioning

Record Pass/Fail + notes for each line. Do not roll out until every line passes.

## A. Before scanning
| # | Check | Pass/Fail | Notes |
|---|---|---|---|
| A1 | StageNow app → About: MX version ≥ 13.3 | | |
| A2 | Join scanner SSID manually; browser → `http://192.168.0.91:8081/test.txt` loads | | |
| A3 | Both APK URLs and the `.bin` URL download in the TC22 browser | | |
| A4 | Router client list: note MAC shown for this TC22 | | |

## B. Stage
| # | Check | Pass/Fail | Notes |
|---|---|---|---|
| B1 | Scan JS PDF417 barcodes in order; profile completes; device reboots itself | | |
| B2 | Time from first scan to reboot (min) | | |

## C. Immediately after reboot (person staging does this)
| # | Check | Pass/Fail | Notes |
|---|---|---|---|
| C1 | Open Grivet Scan Assist — list every permission prompt, tap **Allow** | | |
| C2 | Open SkuStack — list every permission prompt, tap **Allow**; log in works | | |
| C3 | Wi-Fi → SSID → Privacy shows **Use device MAC** (else note "randomized") | | |
| C4 | Router MAC matches Settings → About phone → Wi-Fi MAC | | |

## D. Guide step-40 checklist
| # | Check | Pass/Fail |
|---|---|---|
| D1 | Connected to scanner SSID | |
| D2 | Both apps launch | |
| D3 | Play Store, Chrome, YouTube, YT Music, Drive, Gmail, Google TV, Meet unavailable | |
| D4 | Screen timeout 5 min; portrait locked | |
| D5 | DND off; scan-rejection audio audible | |
| D6 | Apps section, Enterprise Reset, Unknown Sources, Wi-Fi settings restricted | |
| D7 | Bluetooth works; USB file access from PC blocked; battery % visible; Power Off available | |
| D8 | Imager/scanner works | |
| D9 | Factory Reset still reachable? (record — guide says not blocked) | |

## E. Life-cycle tests (do these on the pilot, not later)
| # | Check | Pass/Fail | Notes |
|---|---|---|---|
| E1 | **Wi-Fi change profile:** scan it; device joins test SSID/new passphrase while Wi-Fi UI stays locked | | |
| E2 | **App update:** replace APK on server (same filename, same signing key), scan update profile; new version installed, app data kept | | |
| E3 | **Denied permission recovery:** deny a permission once — can it be fixed without the Apps settings screen? | | |
| E4 | **Re-stage after Enterprise Reset:** MAC + all settings come back | | |
| E5 | Walk far aisles/dock: Wi-Fi stays connected, scans upload | | |
