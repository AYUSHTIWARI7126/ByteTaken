# 3-minute judge demo: SafeZone

**Setup:** the NVIDIA laptop with a USB camera pointed at a floor area. The hazard zone is
marked with tape or a bag. Screen split: the PipeGen live display on the left, the Ops Console
(http://localhost:8770) on the right. Keep a terminal with `mosquitto_sub -t 'safezone/#' -v` ready.

## 0:00 Hook (15 s)
"Most workplace injuries near machines happen when someone steps into a danger zone, and the
CCTV that recorded it was watched by nobody. SafeZone turns that camera into a live safety
sensor."

## 0:15 PipeGen is the engine (60 s), shown in PipeGen
1. **Requirement**: "We described it in one sentence."
2. **Pipeline IR**: walk the node graph: "camera, person detector, tracker, zone and line analytics, MQTT out."
3. **Model**: "[[model]] from CraftifAI's catalog."
4. **Compiler**: "Compiled to TensorRT. FP16 runs at [[X]] FPS; the INT8 engine runs at [[Y]] FPS with [[Z]]% less power, for [[n]] points of accuracy." (Edge Optimization bonus)
5. **Run**: "That's this live app, running on the GPU right now."

## 1:15 Live demo (60 s)
1. Nobody in the zone: the console says **ZONE CLEAR** in green, and the people counter tracks whoever's in view.
2. **Walk into the taped zone.** The box enters the polygon on the live display, the console turns **red**, "PERSON IN HAZARD ZONE", and an incident is logged.
3. Show the terminal: "This is the raw JSON PipeGen publishes over MQTT. A PLC, a siren or a phone alert can subscribe to it."
4. Walk across the safety line: the crossing counter goes up. Step out: back to green.

## 2:15 Close (30 s)
"Everything that sees and decides here was built and runs in PipeGen: requirement, IR, model,
TensorRT compile, DeepStream run. Only metadata leaves the box, so there's no privacy footprint.
Next is the INT8 engine on a Jetson as a pole-mounted unit, plus PPE checks."

---

## Likely judge questions
| Q | A |
|---|---|
| Why INT8? | [[X]]× throughput and lower power, so one edge box can handle more cameras or run on a Jetson. Person presence is robust to the small accuracy loss. |
| False alarms? | The tracker keeps IDs stable, and the alert uses the box's foot point inside the zone. A 3-second hold stops flicker. |
| Latency? | Camera to alert in about [[ ]] ms (pipeline) plus MQTT, well under a second. |
| Privacy? | No frames are stored or sent, only JSON counts and boxes. |
| What did PipeGen do vs. you? | PipeGen generated the whole pipeline, the engines and the run app. We wrote the requirement, tuned the zone and wrote the dashboard that consumes its feed. |
