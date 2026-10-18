# Embedded SF: CraftifAI Physical AI Hackathon · deadline 6:00 pm

## Quick start on the PipeGen laptop (Fedora/Ubuntu + NVIDIA GPU)
```bash
git clone https://github.com/AYUSHTIWARI7126/ByteTaken.git ~/ByteTaken
cd ~/ByteTaken/TrackA_PipeGen
pip3 install --user -r requirements.txt
python3 safety_console.py --demo            # preview: open http://localhost:8770
```
Get updates later with `cd ~/ByteTaken && git pull`.
Then follow [TrackA_PipeGen/RUNBOOK.md](TrackA_PipeGen/RUNBOOK.md) from "TOMORROW". Once the
PipeGen pipeline is publishing MQTT, run the real console:
```bash
python3 safety_console.py --mqtt localhost --topic '#'
```

## PRIMARY PLAN: Track A (PipeGen) → `TrackA_PipeGen/`
**SafeZone**, a workplace hazard-zone safety sentinel. It runs on a friend's NVIDIA laptop with
Ubuntu + PipeGen v0.5.1 and the USB camera from the hardware desk.

| File | What |
|---|---|
| [TrackA_PipeGen/RUNBOOK.md](TrackA_PipeGen/RUNBOOK.md) | **Start here.** Tonight: Ubuntu + PipeGen setup on the NVIDIA laptop. Tomorrow: stage-by-stage plan, the requirement sentence to paste, the evidence checklist |
| [TrackA_PipeGen/SUBMISSION.md](TrackA_PipeGen/SUBMISSION.md) | Form text → https://forms.gle/eJyeCKCG2UH757QZ8 |
| [TrackA_PipeGen/DEMO_SCRIPT.md](TrackA_PipeGen/DEMO_SCRIPT.md) | 3-minute judge demo + Q&A |
| `TrackA_PipeGen/safety_console.py` | Ops Console: `python safety_console.py --demo`, or `--mqtt localhost`, or `--tail <json dir>`, then http://localhost:8770 |

## FALLBACK: Track B (FirmGen) → files in this folder
Use this if PipeGen can't be made to run on the NVIDIA laptop. It runs on this Windows laptop,
and the organisers hand out the ESP32 kit at the hardware desk.

| File | What |
|---|---|
| [02_FirmGen_Runbook.md](02_FirmGen_Runbook.md) | Full day plan for GuardianBand (fall-detection wearable) |
| `01_PRD/GuardianBand_PRD.pdf` | PRD to upload to FirmGen (Lite version for minimal hardware) |
| `03_companion/guardian_console.py` | BLE Caregiver Console (`--demo` to preview) |
| `04_Submission/`, `05_Pitch/` | Form text (https://forms.gle/bnocK9CNLndiZLwf8) and demo script |
| ESP32 USB driver | Not in the repo. CH340 boards: download CH341SER.EXE from wch-ic.com; CP210x boards: silabs.com |

## Other
- `reference/`: official problem statement, FirmGen lab guide, sample PRD
- `tools/md_to_pdf.py`: rebuild a PRD PDF after edits
- Sign-up for both tools: https://developer.craftifai.com/dashboard?tab=downloads
