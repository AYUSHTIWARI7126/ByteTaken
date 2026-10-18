# Track A Runbook: SafeZone (Workplace Safety Sentinel) on PipeGen

**Project:** a site camera watches a work area. PipeGen builds a GPU pipeline that detects and
tracks people, raises an alert the moment anyone enters a **hazard zone**, and counts crossings of
a **safety line**. It publishes alerts over **MQTT** and as **JSON metadata**. The SafeZone Ops
Console turns that feed into a live red/green safety dashboard with an incident log.

**Bonus:** Edge Optimization (an INT8 engine vs FP16, with PipeGen's speed/power/accuracy report).
**Form:** https://forms.gle/eJyeCKCG2UH757QZ8 · **Deadline 4:00 pm**

Track A mandatory items (from the problem statement):
1. All five PipeGen stages: Requirement → Pipeline IR → Model → Compiler → Run (not a notebook script)
2. At least one **TensorRT engine** + PipeGen's **speed report**
3. **Live run** on video/USB camera on the NVIDIA machine
4. **Actionable output**: JSON/MQTT/alerts, not just boxes
5. Evidence: screenshots of the **Pipeline IR node graph** and the **TensorRT speed report**

---

## TONIGHT, on your friend's NVIDIA laptop (Fedora)

### Step 1: Check the GPU (2 min)
In a Fedora terminal:
```bash
lspci | grep -i nvidia     # shows the GPU model
nvidia-smi                 # works only if the NVIDIA driver is installed
```
An RTX card (20xx / 30xx / 40xx / 50xx) is ideal. If it's a GTX 10xx or older, tell me first, because TensorRT INT8 and newer DeepStream may not support it.

### Step 2: Check which OS PipeGen supports (5 min)
Sign in at https://developer.craftifai.com/dashboard?tab=downloads and open the **PipeGen v0.5.1** download.
Note the supported OS. The problem statement says "x86-64 Linux PC … in an X11 desktop session", and NVIDIA
DeepStream officially supports **Ubuntu only**.
- If it offers a Fedora/RPM/Docker/generic-Linux build, try it on Fedora first and skip to Step 4.
- If it's Ubuntu only (most likely), do Step 3.

### Step 3: Install Ubuntu without touching Fedora (≈1–1.5 h)
**Safest option: install Ubuntu onto an external USB SSD/pendrive (≥ 64 GB, ideally a USB-3 SSD).**
You need **two** USB drives: one 8 GB+ stick for the installer, and the external drive Ubuntu lives on.

1. Download the **Ubuntu Desktop ISO**. Use the version the PipeGen page names; if it doesn't say, use **22.04 LTS** (it matches JetPack 6 and DeepStream 7.x).
2. On Fedora, write the ISO to the 8 GB stick with **Fedora Media Writer** ("Select .iso file").
3. Reboot and open the boot menu (usually **F12**, **F11**, **F9** or **Esc**), then boot the installer stick.
4. In the installer:
   - ✅ "Install third-party software for graphics and Wi-Fi" (this installs the NVIDIA driver)
   - If it asks for a **Secure Boot password**, set one and write it down. On the next reboot, a blue "MOK" screen asks for it: choose **Enroll MOK**, then Continue, then enter the password.
   - Installation type: **Something else**. Select **only the external drive** (e.g. `/dev/sdb`, the one with the right size). **Don't select the internal Fedora disk (`nvme0n1`).**
   - "Device for boot loader installation" = **the external drive**.
5. Boot from the external drive (via the boot menu) and log in.
6. **Switch to X11:** log out, click your name, click the ⚙ gear (bottom right), choose **"Ubuntu on Xorg"**, then log in. Check:
   ```bash
   echo $XDG_SESSION_TYPE    # must print: x11
   nvidia-smi                # must show the GPU and driver
   ```
   If `nvidia-smi` fails, run `sudo ubuntu-drivers install` and reboot.

*Alternative:* dual-boot on the internal disk. That means shrinking Fedora's partition, which is riskier. Only do it if your friend is comfortable with it.

### Step 4: Install PipeGen + tools (≈30–60 min, mostly downloads)
1. Install **PipeGen v0.5.1** following the portal's instructions, then sign in.
   ```bash
   pipegen --version         # must print 0.5.1
   ```
2. MQTT broker (the pipeline publishes to it, and the Ops Console reads from it).
   **Fedora (PipeGen installed on Fedora XFCE):**
   ```bash
   sudo dnf install -y mosquitto git python3-pip
   sudo systemctl enable --now mosquitto     # listens on localhost:1883
   pip3 install --user paho-mqtt
   ```
   **Ubuntu:**
   ```bash
   sudo apt update && sudo apt install -y mosquitto mosquitto-clients git python3-pip
   printf "listener 1883\nallow_anonymous true\n" | sudo tee /etc/mosquitto/conf.d/lan.conf
   sudo systemctl restart mosquitto
   mosquitto_sub -t '#' -v &   # leave running; Ctrl+C later
   mosquitto_pub -t test -m hello   # should print "test hello"
   ```
3. Get this project onto the laptop:
   ```bash
   git clone https://github.com/AYUSHTIWARI7126/ByteTaken.git ~/ByteTaken
   cd ~/ByteTaken/TrackA_PipeGen
   pip3 install -r requirements.txt
   python3 safety_console.py --demo   # open http://localhost:8770 and check it animates
   ```
4. **Test videos (keep them under /home, as PipeGen requires):**
   - Record 2–3 phone videos (30–60 s, landscape, phone held still) of people walking across a room. Make one where someone walks into a corner you'll call the "hazard zone", and one with nobody in the zone. Copy them to `~/videos/`.
   - If DeepStream installs with PipeGen, also copy its sample: `cp /opt/nvidia/deepstream/deepstream/samples/streams/sample_720p.mp4 ~/videos/`
5. Create an empty public GitHub repo `safezone-pipegen` on https://github.com/new (the PipeGen export folder goes there).

✅ **Done tonight when:** `pipegen --version` prints 0.5.1, `XDG_SESSION_TYPE=x11`, `nvidia-smi` works, mosquitto echoes, and the videos are in `~/videos`.

**If you're stuck tonight:** send me the exact error text. If Ubuntu or PipeGen can't be made to work by ~1 am, switch back to **Track B** (everything is ready in the main folder) and sleep.

---

## TOMORROW

### 10:00–12:00: PipeGen workshop
Do the official PipeGen lab. It proves your install end to end. Collect the **USB camera** from the hardware desk.
Ask a mentor:
1. "What MQTT topic and message schema does PipeGen's MQTT output use?"
2. "Does PipeGen support ROI/zone and line-crossing analytics (nvdsanalytics), or should we describe it in the requirement?"

### 12:00: Stage 1, Requirement
Paste this as the requirement (adjust if the mentor's answers say otherwise):

> Detect and track people in a workplace safety camera feed from a USB camera (and from video files for testing). Raise an alert whenever a person enters the hazard zone polygon in the right third of the frame, count people crossing the safety line from left to right, and count people currently in the zone. Publish every frame's detections and zone/line analytics as JSON to the MQTT broker at localhost:1883 on topic safezone/events, also save JSON metadata files, and show a live display with boxes, track IDs, the zone and the line drawn on screen. Build FP16 and INT8 TensorRT engines and report speed, power and accuracy for both.

**Simpler fallback**, if PipeGen struggles with zones:
> Detect and track people in a USB camera feed, publish detections as JSON over MQTT to localhost:1883 topic safezone/events and save JSON metadata, with live display. Build an FP16 TensorRT engine.

(The Ops Console can then compute the zone itself with `--zone`, but pipeline-side analytics are much stronger for judging, because PipeGen must be load-bearing.)

### 12:20: Stage 2, Pipeline IR
Review the node graph: source → decoder → streammux → **nvinfer (person detector)** → **tracker** → **analytics (ROI + line crossing)** → OSD → sinks (display + **MQTT/msgbroker** + JSON). Fix anything missing via PipeGen's editor or chat.
📸 **Screenshot the Pipeline IR node graph** (mandatory evidence).

### 12:35: Stage 3, Model
Pick a person detector from CraftifAI's catalog (e.g. PeopleNet or a YOLO person/COCO model). Prefer one that lists **INT8 support**. Use Deep Search only if the catalog has nothing suitable.

### 12:50: Stage 4, Compiler
Compile **FP16** first and get the speed report. 📸 **Screenshot the TensorRT speed report** (mandatory evidence).
Then compile **INT8** (it may ask for calibration images; use frames from your videos) and screenshot its report.
Record the numbers in the table in `SUBMISSION.md`: FPS, latency, power, accuracy for FP16 vs INT8.

### 13:20: Stage 5, Run
Run `run.sh` on a video file first, then on the **USB camera**. Check:
```bash
mosquitto_sub -t 'safezone/#' -v          # JSON messages must be flowing
```
Then start the console. Use `--topic '#'` if PipeGen chose a different topic:
```bash
python3 safety_console.py --mqtt localhost --topic 'safezone/#'
# or, from JSON files:  python3 safety_console.py --tail <pipegen export folder>/<json output dir>
```
Open http://localhost:8770, walk into the zone in front of the camera, and the banner should go **red**.
If the pipeline doesn't report zone counts, start the console with a fallback zone in pixel coordinates (right third of a 1280×720 frame):
`--zone "853,0 1280,0 1280,720 853,720"`

### 14:00: Calibrate the zone to the real room
Mark the hazard zone on the floor at the venue with tape or a bag, and adjust the polygon in PipeGen so it matches what the camera sees.
Re-run. 📹 **Record a phone video**: a person walks in, the screen boxes turn and the console goes red, the person leaves, and the console goes green.

### 14:30: Edge Optimization bonus
Run the INT8 engine live. Screenshot PipeGen's FP16 vs INT8 comparison (speed/power/accuracy). Write one sentence on the trade-off.

### 15:00: Push the PipeGen export folder to GitHub
```bash
cd <pipegen export folder>
git init && git add . && git commit -m "SafeZone PipeGen export"
git branch -M main
git remote add origin https://github.com/AYUSHTIWARI7126/safezone-pipegen.git
git push -u origin main
```
Also copy `TrackA_PipeGen/` (the console) into the repo as `console/` and push again. Put the screenshots and videos in an `evidence/` folder.

### 15:20: Submit
Fill in `SUBMISSION.md` and paste it into https://forms.gle/eJyeCKCG2UH757QZ8. **Submit by 15:45.**

---

## Evidence checklist
- [ ] Requirement stage screenshot
- [ ] **Pipeline IR node graph** (mandatory)
- [ ] Model selection screen
- [ ] **TensorRT speed report**, FP16 (mandatory) and INT8 (bonus)
- [ ] Live display: boxes + zone + line on the USB camera feed
- [ ] `mosquitto_sub` terminal showing the JSON flowing
- [ ] Ops Console red alert + incident log
- [ ] Phone video of the full intrusion → alert → clear loop
- [ ] GitHub repo with the PipeGen export folder

## Fallback ladder (never restart from scratch)
1. INT8 fails to calibrate: submit FP16 only and skip the bonus.
2. Zone analytics not supported in PipeGen: use the simpler requirement plus the console's `--zone`, and say honestly that zone logic is in the consumer.
3. MQTT output not working: use JSON metadata files with `safety_console.py --tail`.
4. USB camera not recognised: run on your recorded video (still counts as a live run on the GPU).
