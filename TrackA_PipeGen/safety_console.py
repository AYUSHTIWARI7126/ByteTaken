"""SafeZone Safety Ops Console (Track A companion).

Consumes the actionable output of the PipeGen/DeepStream pipeline and turns it into a live
safety dashboard at http://localhost:8770 with an incident log (incidents.jsonl).
It does no vision itself: detection, tracking and zone/line analytics come from PipeGen.

    python safety_console.py --mqtt 192.168.1.20 --topic "#"   # MQTT feed from the pipeline
    python safety_console.py --tail ~/pipegen_export/output    # JSON metadata files/dir
    python safety_console.py --demo                            # simulated feed, no GPU needed

Message parsing is tolerant: DeepStream "minimal" schema (objects as "id|x1|y1|x2|y2|label"),
DeepStream "full" schema (object/analyticsModule), nvdsanalytics fields (ROI counts, line
crossings), or any JSON with a list of objects carrying a label/class field.
"""
import argparse
import json
import random
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_PATH = HERE / "incidents.jsonl"
PERSON_LABELS = {"person", "people", "pedestrian", "human", "worker"}
QUIET_AFTER_S = 3  # zone counts as clear when no intrusion is reported for this long

lock = threading.Lock()
status = {"source": "-", "messages": 0, "last_msg": 0.0, "persons": 0, "in_zone": 0,
          "line_crossings": 0, "alert": False, "last_alert": 0.0, "last_raw": None}
history = deque(maxlen=120)  # (t, persons, in_zone) for the sparkline
zone_polygon = None          # optional fallback [(x, y), ...] in frame pixels


def point_in_polygon(x, y, poly):
    inside, j = False, len(poly) - 1
    for i, (xi, yi) in enumerate(poly):
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def find_key(obj, predicate, depth=0):
    """Yield (key, value) pairs anywhere in nested JSON whose key matches predicate."""
    if depth > 6:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if predicate(k.lower()):
                yield k, v
            yield from find_key(v, predicate, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            yield from find_key(v, predicate, depth + 1)


def extract_objects(msg):
    """Return a list of (label, bbox or None) from one pipeline message."""
    out = []
    for item in msg.get("objects", []) if isinstance(msg.get("objects"), list) else []:
        if isinstance(item, str):  # minimal schema: "trackid|x1|y1|x2|y2|label|..."
            parts = item.split("|")
            if len(parts) >= 6:
                try:
                    out.append((parts[5].strip().lower(), tuple(float(p) for p in parts[1:5])))
                except ValueError:
                    out.append((parts[5].strip().lower(), None))
        elif isinstance(item, dict):
            out.append(dict_object(item))
    obj = msg.get("object")
    if isinstance(obj, dict):  # full schema: one object per message
        out.append(dict_object(obj))
    if not out:  # generic: any list of dicts that carry a label
        for _, v in find_key(msg, lambda k: k in {"detections", "objs", "frame_objects", "obj"}):
            if isinstance(v, list):
                out += [dict_object(d) for d in v if isinstance(d, dict)]
    return out


def dict_object(d):
    label = next((str(d[k]) for k in ("label", "class", "class_name", "classname", "objectType", "type")
                  if k in d), "")
    if not label and "person" in d:
        label = "person"
    box = d.get("bbox") or d.get("box") or d.get("rect")
    bbox = None
    if isinstance(box, dict):
        keys = {k.lower(): v for k, v in box.items()}
        try:
            if "topleftx" in keys:
                bbox = (keys["topleftx"], keys["toplefty"], keys["bottomrightx"], keys["bottomrighty"])
            elif "left" in keys:
                bbox = (keys["left"], keys["top"], keys["left"] + keys["width"], keys["top"] + keys["height"])
        except KeyError:
            bbox = None
    elif isinstance(box, (list, tuple)) and len(box) == 4:
        bbox = tuple(box)
    return label.lower(), bbox


def sum_numbers(value):
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, dict):
        return sum(sum_numbers(v) for v in value.values())
    if isinstance(value, list):
        return sum(sum_numbers(v) for v in value)
    return 0


def handle_message(msg, source):
    objects = extract_objects(msg)
    persons = [o for o in objects if o[0] in PERSON_LABELS or "person" in o[0]]

    # Zone occupancy and line crossings reported by the pipeline (nvdsanalytics or custom fields).
    roi = [v for _, v in find_key(msg, lambda k: "roi" in k or "inzone" in k or "in_zone" in k
                                  or "zone" == k or "intrusion" in k)]
    in_zone = int(sum_numbers(roi)) if roi else None
    lc = [v for _, v in find_key(msg, lambda k: "linecross" in k or k.startswith("lc") or "crossing" in k)]
    crossings = int(sum_numbers(lc)) if lc else None
    explicit_alert = any(bool(v) for _, v in find_key(msg, lambda k: k in {"alert", "alarm", "violation"}))

    if in_zone is None and zone_polygon:  # fallback: foot point of each person box
        in_zone = sum(1 for _, b in persons if b and point_in_polygon((b[0] + b[2]) / 2, b[3], zone_polygon))

    now = time.time()
    with lock:
        prev_alert = status["alert"]
        status.update(source=source, messages=status["messages"] + 1, last_msg=now,
                      persons=len(persons), last_raw=msg, in_zone=in_zone or 0)
        if crossings is not None:
            status["line_crossings"] = max(status["line_crossings"], crossings)
        if (in_zone or 0) > 0 or explicit_alert:
            status["last_alert"] = now
        status["alert"] = now - status["last_alert"] < QUIET_AFTER_S
        history.append((round(now, 1), len(persons), status["in_zone"]))
        snapshot = dict(status)
    if snapshot["alert"] != prev_alert:
        log_incident("ZONE INTRUSION" if snapshot["alert"] else "ZONE CLEAR", snapshot)


def tick_quiet():
    """Clear the alert when intrusion reports stop arriving."""
    while True:
        time.sleep(1)
        with lock:
            was = status["alert"]
            status["alert"] = time.time() - status["last_alert"] < QUIET_AFTER_S
            snapshot = dict(status)
        if was and not snapshot["alert"]:
            log_incident("ZONE CLEAR", snapshot)


def log_incident(event, snap):
    rec = {"time": datetime.now().isoformat(timespec="seconds"), "event": event,
           "persons": snap["persons"], "in_zone": snap["in_zone"],
           "line_crossings": snap["line_crossings"], "source": snap["source"]}
    print(f"[{rec['time'][11:]}] {event}  persons={rec['persons']} in_zone={rec['in_zone']} "
          f"crossings={rec['line_crossings']}", flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    if event == "ZONE INTRUSION":
        print("\a", end="", flush=True)


# ---- inputs -----------------------------------------------------------------------------

def run_mqtt(host, port, topic):
    import paho.mqtt.client as mqtt

    def on_connect(client, userdata, flags, reason_code, properties=None):
        print(f"MQTT connected to {host}:{port}, subscribing to '{topic}'", flush=True)
        client.subscribe(topic)

    def on_message(client, userdata, m):
        try:
            handle_message(json.loads(m.payload.decode("utf-8", "replace")), f"mqtt:{m.topic}")
        except (json.JSONDecodeError, AttributeError):
            pass

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect, client.on_message = on_connect, on_message
    client.connect(host, port, keepalive=30)
    client.loop_forever()


def run_tail(path):
    """Follow JSON metadata: a .jsonl file, a .json file, or a directory of either."""
    path = Path(path).expanduser()
    offsets, mtimes = {}, {}
    print(f"Following JSON metadata in {path}", flush=True)
    while True:
        files = sorted(path.glob("**/*.json*")) if path.is_dir() else [path]
        for f in files:
            try:
                st = f.stat()
            except FileNotFoundError:
                continue
            if mtimes.get(f) == st.st_mtime:
                continue
            mtimes[f] = st.st_mtime
            text = f.read_text(encoding="utf-8", errors="replace")
            start = offsets.get(f, 0) if st.st_size >= offsets.get(f, 0) else 0
            chunk, offsets[f] = text[start:], len(text)
            parsed_any = False
            for line in chunk.splitlines():
                line = line.strip().rstrip(",")
                if line.startswith("{"):
                    try:
                        handle_message(json.loads(line), f"file:{f.name}")
                        parsed_any = True
                    except json.JSONDecodeError:
                        pass
            if not parsed_any:  # whole-file JSON (one frame, or a list of frames)
                try:
                    doc = json.loads(text)
                except json.JSONDecodeError:
                    continue
                for msg in doc if isinstance(doc, list) else [doc]:
                    if isinstance(msg, dict):
                        handle_message(msg, f"file:{f.name}")
        time.sleep(0.5)


def run_demo():
    """DeepStream-minimal-schema messages: people walk across a 1280x720 frame."""
    global zone_polygon
    zone_polygon = zone_polygon or [(800, 300), (1250, 300), (1250, 710), (800, 710)]
    people = []
    print("Demo mode: simulated PipeGen MQTT feed", flush=True)
    frame = 0
    while True:
        frame += 1
        if random.random() < 0.04 and len(people) < 5:
            people.append({"id": random.randint(1, 999), "x": -60.0, "y": random.uniform(330, 600),
                           "v": random.uniform(6, 14)})
        for p in people:
            p["x"] += p["v"]
        people = [p for p in people if p["x"] < 1300]
        objs = [f"{p['id']}|{p['x']:.0f}|{p['y'] - 180:.0f}|{p['x'] + 70:.0f}|{p['y']:.0f}|person" for p in people]
        handle_message({"version": "4.0", "id": frame, "@timestamp": datetime.now().isoformat(),
                        "sensorId": "site-cam-01", "objects": objs}, "demo")
        time.sleep(0.2)


# ---- dashboard --------------------------------------------------------------------------

PAGE = (HERE / "safety_dashboard.html").read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            with lock:
                snap = {k: v for k, v in status.items() if k != "last_raw"}
                snap["online"] = time.time() - status["last_msg"] < 5
                snap["history"] = list(history)
                snap["last_raw"] = json.dumps(status["last_raw"])[:1500] if status["last_raw"] else ""
            incidents = []
            if LOG_PATH.exists():
                incidents = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines()[-20:]][::-1]
            snap["incidents"] = incidents
            body, ctype = json.dumps(snap), "application/json"
        elif self.path == "/":
            body, ctype = PAGE, "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def main():
    global zone_polygon
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--mqtt", metavar="HOST", help="MQTT broker host (port via --mqtt-port)")
    src.add_argument("--tail", metavar="PATH", help="JSON metadata file or directory to follow")
    src.add_argument("--demo", action="store_true", help="simulated feed")
    ap.add_argument("--mqtt-port", type=int, default=1883)
    ap.add_argument("--topic", default="#")
    ap.add_argument("--zone", help='fallback hazard zone in frame pixels, e.g. "800,300 1250,300 1250,710 800,710"'
                                   " (only used when the pipeline does not report zone counts)")
    ap.add_argument("--port", type=int, default=8770)
    args = ap.parse_args()
    if args.zone:
        zone_polygon = [tuple(float(v) for v in pt.split(",")) for pt in args.zone.split()]

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(target=tick_quiet, daemon=True).start()
    print(f"Dashboard: http://localhost:{args.port}   Incident log: {LOG_PATH}", flush=True)
    try:
        if args.demo:
            run_demo()
        elif args.tail:
            run_tail(args.tail)
        else:
            run_mqtt(args.mqtt, args.mqtt_port, args.topic)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
