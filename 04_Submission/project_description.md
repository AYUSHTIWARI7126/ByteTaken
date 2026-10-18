# Submission text: paste into the FirmGen form

> Fill in every `[[ ]]` on the day. Delete anything you didn't actually achieve. Judges check evidence.

**Project name:** GuardianBand: on-device fall detection and SOS wearable

**Team:** [[names]]

**Track:** Track B: FirmGen (Action). Suggested problems #2 (Fall Detection & Elder Care) and #7 (Wearable Health Tracker).

**Bonus targeted:** Live Intelligence [[delete if not achieved]]

**Repository:** https://github.com/AYUSHTIWARI7126/guardianband-firmgen, branch `FG-guardianband` (pushed from FirmGen's Git view)

---

### Problem
Falls are the leading cause of injury-related death among people over 65, and a person who
can't get up after a fall is often found hours later. Camera-based monitoring raises privacy
concerns and needs installed infrastructure. Commercial fall-alert pendants are expensive and
tied to subscriptions.

### Solution
GuardianBand is a sub-$10 ESP32 wearable that detects falls **on the device**. It runs a
three-phase detector (free-fall < 0.4 g, then impact > 2.5 g within 500 ms, then 2 s of
stillness) on a 100 Hz MPU6050 stream. It then gives the wearer a **10-second cancel window**
(buzzer + LED) to avoid false alarms, escalates to **FALL_CONFIRMED**, and offers a manual
**SOS** long-press. Its live safety state is broadcast in **BLE advertisements**, so any nearby
phone or laptop sees it instantly. There's no pairing, no Wi-Fi, no cloud and no camera.

An 8-byte manufacturer-data protocol (version, state, event counter, impact peak in g, uptime)
is decoded by our Caregiver Console. The console is a laptop dashboard that turns red and beeps
on an alert and logs every incident to JSON. Any phone running nRF Connect can read the same
data.

### How FirmGen is load-bearing
FirmGen built the entire firmware from our own PRD (`01_PRD/GuardianBand_PRD.pdf`):
- **PRD → requirements:** FirmGen generated [[N]] requirements in [[N]] categories ([[N]] Explicit, [[N]] Inferred). We confirmed [[N]] inferred requirements (e.g. [[I2C error handling / watchdog]]) and rejected [[N]] out-of-scope ones (e.g. GATT services, NVS persistence, sleep modes), then froze the baseline.
- **Task lists and acceptance criteria:** each criterion is classified as host-testable (the fall-detection algorithm is pure C by design) or on-target (BLE visibility, buzzer, drop test).
- **Implementation:** Auto Mode generated modular ESP-IDF v5.5 / NimBLE firmware (sensor driver, fall-detection logic, alert output, button handler, BLE advertiser) following the BARR-C coding standard, then built, flashed and monitored it on our ESP32.
- **Iteration:** [[describe 1–2 Direct Prompt fixes, e.g. threshold tuning from UART evidence]].
- **Verification:** requirement-linked unit tests ([[X/Y passing]]), a generated design document (state machine and BLE sequence), and the **traceability report** linking every requirement to its criteria, code and tests.
- **Live Intelligence:** telemetry injected by FirmGen streams the RTOS task and system state live while we drop the device. [[delete if not achieved]]

### Hardware
ESP32 DevKit (ESP32-WROOM-32), MPU6050 (I2C, GPIO21/22), active buzzer (GPIO25), LED (GPIO26),
on-board BOOT button (GPIO0).

### Evidence (attached / in repo `evidence/`)
- FirmGen traceability report: [[file name]]
- UART Monitor log: boot banner, `BLE ADVERTISING STARTED`, state transitions
- nRF Connect screenshot: `GuardianBand_[[XX]]` with manufacturer data `FF FF 01 …`
- Video: drop → FALL_SUSPECTED → cancel; drop → FALL_CONFIRMED → console alert; SOS
- Unit test report, design document, frozen requirement table, Live Intelligence screenshot

### Acceptance results
| PRD criterion | Result |
|---|---|
| 1 Boot + advertising | [[PASS]] |
| 2 Name matches BT MAC | [[PASS]] |
| 3 Rest reading ≈ 1 g | [[PASS]] |
| 4 Drop → FALL_SUSPECTED ≤ 3 s | [[PASS]] |
| 5 Cancel by short press | [[PASS]] |
| 6 Escalation after 10 s | [[PASS]] |
| 7 Acknowledge by 3 s press | [[PASS]] |
| 8 SOS by 2 s press | [[PASS]] |
| 9 UART `f` / `s` test hooks | [[PASS]] |
| 10 State visible in adverts ≤ 1 s | [[PASS]] |
| 11 No false alarm in 30 s of normal motion | [[PASS]] |
| 12 Host unit tests of fall detector | [[PASS]] |

### What's next
Pair GuardianBand with a PipeGen fall-pose pipeline for Closed-Loop room coverage, add a
BLE-to-SMS gateway, and run on a battery-powered ESP32-C3 in a wrist strap.
