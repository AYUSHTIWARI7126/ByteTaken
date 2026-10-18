# Hackathon Day Runbook: GuardianBand on FirmGen (Track B)

Deadline **4:00 pm**. FirmGen must do the real work: requirements, code, build, flash, tests and
traceability all come from FirmGen. The judges will mark down anything that looks bolted on, and
simulation-only projects are not eligible.

---

## TONIGHT (do not skip, setup on the day eats hours)

- [ ] Sign up and download **FirmGen v0.4.1**: https://developer.craftifai.com/dashboard?tab=downloads
- [ ] Install the prerequisites from the zipped prerequisites guide, install FirmGen, launch it, sign in.
- [ ] Let it auto-install **ESP-IDF v5.5**. If you have another ESP-IDF on this PC, make sure FirmGen uses v5.5.
- [ ] Create an **empty GitHub repo** at https://github.com/new?name=guardianband-firmgen&visibility=public (no README). FirmGen pushes to `https://github.com/AYUSHTIWARI7126/guardianband-firmgen.git`.
- [ ] Phone: install **nRF Connect for Mobile** (Nordic). It shows the device name **and** the manufacturer data bytes.
- [ ] Laptop: `cd 03_companion` then `python guardian_console.py --demo`, open http://localhost:8765 and check the dashboard animates. (Already tested once, works.)
- [ ] Charge the laptop and phone. Bring a USB **data** cable (not charge-only) and a cushion or folded jacket for the drop test.
- [ ] If you own an ESP32 board, run the lab PRD tonight to shake out driver/COM-port problems.

## 10:00–12:00: Workshop

Do the official FirmGen lab with `ESP32_BLE_FirmGen_Simple_PRD.pdf`. It proves your toolchain,
board, COM port and flashing all work. While you're at the hardware desk, collect your kit:
- ESP32 board. Check which chip it is (**ESP32-WROOM / DevKitC / DevKit V1**, or S3/C3; see pin table below).
- **MPU6050** module, **active buzzer**, **LED + 220 Ω resistor**, jumper wires, breadboard.
- No MPU6050 in the kit? Ask for any accelerometer. If there isn't one, use **`GuardianBand_Lite_PRD.pdf`**.

Ask a mentor one question: *"Does Live Intelligence telemetry work on ESP32 over USB, or only with ST-Link/J-Link?"* Their answer tells you whether to plan for that bonus.

## 12:00: Create the project (5 min)

| Field | Value |
|---|---|
| Project name | `GuardianBand` |
| Platform / Board | ESP32 / your board, then click **Verify** |
| Toolchain | ESP-IDF v5.5 |
| Coding guideline | **BARR-C** (looks professional; judges like standards) |
| Board schematic / Sources | Optional: add the MPU6050 datasheet PDF as a source if you have it (R4: lets FirmGen cite registers) |

## 12:05: Upload PRD, then generate requirements

Draft PRD, then **I have a document**, then upload `01_PRD/GuardianBand_PRD.pdf`, then **Generate requirements**.

**If your pins differ** (kit board is S3/C3, or a different buzzer), edit `01_PRD/GuardianBand_PRD.md`, then run
`python tools/md_to_pdf.py 01_PRD/GuardianBand_PRD.md` and upload the new PDF.

| Signal | ESP32 (WROOM/DevKitC) | ESP32-S3 | ESP32-C3 |
|---|---|---|---|
| I2C SDA / SCL | 21 / 22 | 8 / 9 | 6 / 7 |
| Buzzer | 25 | 4 | 4 |
| LED | 26 | 5 | 5 |
| Button (BOOT) | 0 | 0 | 9 |

Passive buzzer instead of active? Change requirement wording to "drive the buzzer with a 2 kHz PWM (LEDC) tone".

## 12:15: Review and freeze (≈10 min). This is where you win or lose time

**Check that every Explicit requirement exists:** 28 numbered requirements, the 4 states, the 8-byte advertising layout, UART messages, the `f`/`s` test hook, and NimBLE.

**Confirm (keep) inferred requirements like:** I2C error handling, task stack/priority definitions, a watchdog, a startup log of the threshold values, mutex/queue between the sensor task and the state machine.

**Reject inferred requirements that add scope** (each one adds build time):
GATT services or characteristics · connections, pairing, bonding · Wi-Fi or MQTT · NVS or flash persistence · deep or light sleep, power management · battery measurement · OLED or display · OTA · step counting · gyroscope-based fusion.

Then click **Freeze**.

## 12:25: Task lists, then Criteria (5 min)

Click **Task lists**, then **Criteria**. Check that the fall-detection criteria are marked **host-testable**
(PRD req 27 makes the algorithm pure C for exactly this reason). BLE visibility should be **on-target**.

## 12:30: Start implementation in **Auto Mode** (≈60–90 min)

Before you start: plug in the ESP32 and note its COM port. Don't touch Build/Flash/Monitor while Auto Mode runs.

**While it runs:**
1. **Git**: top bar, then Git. Remote = `https://github.com/AYUSHTIWARI7126/guardianband-firmgen.git`, branch = `guardianband` (becomes `FG-guardianband`, and you can't rename it later), author = your name and email.
2. **Wire the hardware** (USB unplugged while wiring, then re-plug):
   ```
   MPU6050 VCC -> 3V3     MPU6050 GND -> GND
   MPU6050 SDA -> GPIO21  MPU6050 SCL -> GPIO22
   GPIO25 -> buzzer (+), buzzer (-) -> GND
   GPIO26 -> 220Ω -> LED long leg, LED short leg -> GND
   Button = on-board BOOT (no wiring)
   ```
   If FirmGen needs to flash while the board is unplugged, plug it back in and let it retry.
3. **Screenshot as you go** (see Evidence list below). Requirement table, task lists, criteria, Firmware Topology, pipeline phases.
4. Start the companion: `python 03_companion/guardian_console.py` and open http://localhost:8765.

If it stops part way: use **continue** in the Req. panel. If you hit a context-window error, open a new chat in the same project and say *"continue from the previous chat"*. **Never restart the project.**

## ~14:00: Validate on the board (Monitor, 115200)

Work through the PRD acceptance criteria in order and **record a phone video of each one**:

| # | Do | Expect |
|---|---|---|
| 1 | Press EN/reset | Banner, MAC, `GuardianBand_XX`, `BLE ADVERTISING STARTED` |
| 2 | nRF Connect scan | `GuardianBand_XX`; XX = last 2 digits of the BT MAC on UART (the BT MAC differs from the Wi-Fi MAC; that's expected) |
| 3 | Leave on table | `ACC |a|=0.9x–1.0x g` every second |
| 4 | Drop ~50 cm onto cushion, leave still | FALL_SUSPECTED within 3 s, beeping |
| 5 | Short-press BOOT | `FALL CANCELLED BY USER` |
| 6 | Repeat drop, wait 10 s | FALL_CONFIRMED, continuous alarm, dashboard turns red |
| 7 | Hold BOOT 3 s | Back to NORMAL |
| 8 | Hold BOOT 2 s | SOS |
| 9 | Type `f`, then `s` in Monitor | Simulated fall / SOS |
| 10 | nRF Connect → manufacturer data | `FF FF 01 0X ...` state byte changes |
| 11 | Shake gently, walk with it 30 s | No false alarm |

**Something fails? Use a Direct Prompt in FirmGen**, scoped tightly. Copy-paste prompts:
- *"Show me the runtime evidence from the last deploy and identify the first failure the device reported."*
- *"The drop test does not trigger FALL_SUSPECTED. Print the min and max |a| over each 500 ms window on UART so I can tune the thresholds; change nothing else."*
- *"Lower the impact threshold from 2.50 g to 2.0 g in the configuration header only, then rebuild, flash and monitor."*
- *"Fix only the first root-cause build error, preserve the current architecture, and redeploy."*
- *"MPU6050 not detected: scan the I2C bus at boot and print every responding address."* (Many cheap modules sit at 0x69 when AD0 is high.)

## ~14:30: Live Intelligence bonus

Live Intelligence panel, then **Enable Telemetry**. It injects, rebuilds, flashes and streams. Show the
**RTOS / System Monitor** (tasks, CPU, stack/heap) live while you drop the device. Screenshot it.
If it fails or needs a debug probe you don't have, skip it. Don't burn more than 25 minutes here.

## ~15:00: Artifacts, traceability, push (do not leave this to 15:50)

1. Artifacts, then **Unit Tests**. Expect tests for the fall-detection sequences (PRD acceptance criterion 12). Screenshot the results.
2. Artifacts, then **Design Doc**. Find the state machine and the BLE sequence diagrams and screenshot them.
3. Open the **traceability report** in `sources/` (.html/.xlsx). Follow REQ 18 (the name) and REQ 5–8 (fall) end to end. Save the file.
4. Git view: review the diffs, commit, **push**. Open GitHub in the browser and confirm the files are there.
5. Copy all screenshots, the videos, the traceability report and `incidents.jsonl` into `04_Submission/evidence/`.

## 15:20: Submit (FirmGen form)

https://forms.gle/bnocK9CNLndiZLwf8. Paste from `04_Submission/project_description.md`. **Submit by 15:45.**

---

## Evidence checklist (judges: "a command that completes is not the same as a system that works")

- [ ] Frozen requirements table (Explicit vs Inferred visible)
- [ ] Task lists + acceptance criteria screen
- [ ] Firmware Topology screenshot
- [ ] Pipeline showing Planning → Coding → Building → Flashing → Monitoring complete
- [ ] Monitor/UART log: boot banner + state changes (copy the text too)
- [ ] nRF Connect screenshot: name + manufacturer data
- [ ] Video: drop → beep → cancel; drop → confirmed alarm → dashboard red
- [ ] Unit test results report
- [ ] Design doc (state machine page)
- [ ] **Traceability report** (mandatory)
- [ ] Live Intelligence screenshot (bonus)
- [ ] GitHub repo URL with the `FG-guardianband` branch

## Fallback ladder (keep moving, never restart)

1. Fall detection unreliable at 14:30? Demo it with the `f` UART hook plus one real drop, and tell the judges the thresholds are configurable and unit-tested.
2. MPU6050 missing or dead? Start a new FirmGen project with `GuardianBand_Lite_PRD.pdf` (much smaller, ≈30–40 min in Auto Mode).
3. Auto Mode still running at 15:00? Let it finish. Meanwhile prepare the form text. Submit the traceability report as it stands.
