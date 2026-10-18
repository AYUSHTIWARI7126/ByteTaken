# Submission text: paste into the PipeGen form (https://forms.gle/eJyeCKCG2UH757QZ8)

> Fill in every `[[ ]]` on the day and delete anything you didn't achieve. Judges check evidence.

**Project name:** SafeZone: real-time hazard-zone safety sentinel

**Team:** [[names]]

**Track:** Track A: PipeGen (Perception). Suggested problem #1: Workplace Safety Sentinel.

**Bonus targeted:** Edge Optimization (INT8 TensorRT engine vs FP16) [[delete if not achieved]]

**Repository:** https://github.com/AYUSHTIWARI7126/safezone-pipegen (PipeGen export folder + console + evidence)

---

### Problem
Workers walk into hazard zones (around presses, forklifts, robot cells, open pits) and nobody
notices until there's an incident. CCTV records everything, but nobody is watching it live, and
manual safety walks happen only a few times a shift.

### Solution
SafeZone turns any existing site camera into a live safety sensor. An edge GPU pipeline built
with CraftifAI PipeGen detects and tracks every person and checks each one against a configured
hazard-zone polygon and a safety line. It publishes the result as an actionable feed: JSON
events over MQTT plus JSON metadata files. Our SafeZone Ops Console subscribes to that feed and
shows a live red/green safety banner, occupancy and crossing counters, and a timestamped
incident log that a supervisor, a PLC or a siren can act on. Only metadata leaves the edge box;
no video is stored or sent.

### PipeGen pipeline (all five stages)
| Stage | What we did |
|---|---|
| Requirement | "Detect and track people … alert when a person enters the hazard zone … count line crossings … publish JSON over MQTT … FP16 and INT8 engines" |
| Pipeline IR | [[source]] → nvstreammux → nvinfer ([[model]]) → nvtracker ([[tracker]]) → [[nvdsanalytics: ROI + line crossing]] → nvdsosd → sinks: display + MQTT ([[topic]]) + JSON metadata |
| Model | [[model name]] from the CraftifAI catalog ([[classes]]), ONNX |
| Compiler | TensorRT engines: FP16 and INT8 |
| Run | DeepStream app via `run.sh`, live on a USB camera ([[resolution/fps]]) and on recorded site videos |

**Inputs:** USB camera ([[model]]), recorded MP4 site footage
**Outputs:** live display with boxes, track IDs, zone and line overlay · MQTT JSON events · JSON metadata files · Ops Console alerts and incident log
**Hardware:** [[laptop model]], NVIDIA [[GPU]], Ubuntu [[version]], PipeGen v0.5.1

### TensorRT results (from PipeGen's reports)
| Precision | FPS | Latency (ms) | Power (W) | Accuracy ([[metric]]) |
|---|---|---|---|---|
| FP16 | [[ ]] | [[ ]] | [[ ]] | [[ ]] |
| INT8 | [[ ]] | [[ ]] | [[ ]] | [[ ]] |

**Trade-off:** [[e.g. INT8 gave 1.8× FPS and 30% less power for a 1.2-point accuracy drop, which is acceptable for presence detection, where a person is visible across many frames]].

### Evidence (in repo `evidence/`)
- Pipeline IR node graph screenshot
- TensorRT speed reports (FP16, INT8)
- Live display screenshot (zone + line overlay)
- `mosquitto_sub` capture of the JSON events
- Ops Console alert screenshot + `incidents.jsonl`
- Video: person enters zone → alert in [[<1 s]] → leaves → clear

### Why PipeGen is load-bearing
All perception (detection, tracking, zone and line analytics) and all of the actionable output
are generated and run by the PipeGen pipeline on the GPU. The Ops Console only displays the feed
PipeGen publishes. Without the pipeline there's nothing to show.

### What's next
Deploy the INT8 engine on a Jetson Orin Nano as a pole-mounted unit, add PPE (helmet/vest)
detection via Deep Search, and close the loop with a FirmGen ESP32 siren/beacon that lights up
when the zone is breached.
