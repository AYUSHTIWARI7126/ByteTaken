# 3-minute judge demo: GuardianBand

**Setup on the table:** ESP32 wired up on the breadboard, a cushion, the laptop with two windows
side by side (FirmGen Monitor on the left, Caregiver Console http://localhost:8765 on the right),
and the phone with nRF Connect open.

## 0:00 Hook (15 s)
"One in four people over 65 falls every year. The worst outcome isn't the fall itself. It's lying
on the floor for hours because nobody knows. GuardianBand is a ten-dollar wearable that detects
the fall itself and tells everyone nearby, with no camera, no Wi-Fi and no app pairing."

## 0:15 FirmGen is the engine (45 s). Show the FirmGen window
- "We wrote this PRD." Show the PRD: 28 requirements, 12 acceptance criteria.
- "FirmGen turned it into [[N]] requirements. Here's an Explicit one, and here's an Inferred one we accepted, a watchdog. We rejected GATT and sleep modes as scope creep, then froze."
- Show the Firmware Topology: "Five modules. The fall detector is pure C, so FirmGen could unit-test it on the host."
- Show the traceability report and click the GuardianBand_XX name requirement through to its code and test.

## 1:00 Live demo (75 s)
1. Point to the Monitor: `ACC |a|=1.00 g`. Point to the phone: `GuardianBand_XX` is visible.
2. **Drop it onto the cushion.** Monitor shows `STATE NORMAL -> FALL_SUSPECTED`, the buzzer beeps, the console turns amber.
3. "False alarm? Tap the button." Short-press BOOT: `FALL CANCELLED BY USER`.
4. **Drop again, hands off.** After 10 s: FALL_CONFIRMED, continuous alarm, the console turns **red** and the laptop beeps. Show the phone's manufacturer data: state byte `02`.
5. Hold BOOT 3 s to acknowledge. Hold BOOT 2 s for SOS.
6. *(Bonus)* Live Intelligence panel: "This is the RTOS state of the board right now, streamed by telemetry FirmGen injected."

*If the drop doesn't trigger:* type `f` in the Monitor ("our test hook from requirement 26"),
and explain that the thresholds sit in one config header and are covered by unit tests.

## 2:15 Close (30 s)
"Everything on this board came out of FirmGen's requirements-driven flow, from PRD to frozen
requirements to code, flash, tests and traceability. Every behaviour you just saw traces back to
a requirement ID. Next, we'd pair it with a PipeGen fall-pose camera for closed-loop room coverage."

---

## Likely judge questions
| Q | A |
|---|---|
| Why BLE advertising, not a connection? | Any number of receivers can see the alert at once, with no pairing and lowest power. Our state changes appear within 500 ms. |
| False positives? | It needs three phases in order (free-fall, then impact, then stillness), plus a 10 s cancel window. We tested 30 s of walking and shaking with no trigger (criterion 11). |
| What did FirmGen infer that you didn't write? | [[fill in from the Req. tab]] |
| What did you reject, and why? | GATT, NVS and sleep. They're out of scope, and every extra requirement costs build time and adds risk. |
| What do the tests cover vs. not cover? | The host tests cover the detection logic sequences. Electrical, BLE and timing behaviour is verified on the target with the Monitor and the scanner. Traceability completeness isn't the same as tests passing. |
| Security? | Advertising is unauthenticated by design for this demo. Next step: a rolling HMAC token in the payload. |
| Why does the scanner MAC differ from UART? | The ESP32 derives separate MACs per interface. We print the Bluetooth MAC, which is the one that's advertised. |
