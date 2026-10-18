"""GuardianBand Caregiver Console.

Listens for GuardianBand BLE advertisements (no pairing), decodes the manufacturer data defined
in the PRD (requirement 19), and shows a live dashboard at http://localhost:8765. State changes
are written to incidents.jsonl and alerts beep on the laptop.

    python guardian_console.py            # real BLE scanning (Windows/macOS/Linux)
    python guardian_console.py --demo     # simulated device, no hardware needed
"""
import argparse
import asyncio
import json
import random
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

COMPANY_ID = 0xFFFF
PROTOCOL_VERSION = 0x01
STATES = {0: "NORMAL", 1: "FALL_SUSPECTED", 2: "FALL_CONFIRMED", 3: "SOS"}
ALERT_STATES = {"FALL_CONFIRMED", "SOS"}
OFFLINE_AFTER_S = 15
HERE = Path(__file__).resolve().parent
LOG_PATH = HERE / "incidents.jsonl"

devices = {}  # address -> latest decoded record
lock = threading.Lock()


def decode(payload):
    """Decode manufacturer data bytes that follow the 0xFFFF company ID.

    Layout: [version, state, event_counter, peak_g_x10, uptime_div10 (uint16 LE)].
    Returns None for payloads that are not GuardianBand protocol v1.
    """
    if len(payload) < 6 or payload[0] != PROTOCOL_VERSION:
        return None
    return {
        "state": STATES.get(payload[1], f"UNKNOWN({payload[1]})"),
        "events": payload[2],
        "peak_g": payload[3] / 10,
        "uptime_s": int.from_bytes(payload[4:6], "little") * 10,
    }


def beep(state):
    if sys.platform != "win32":
        print("\a", end="", flush=True)
        return
    import winsound
    pattern = [(1800, 400)] * 3 if state in ALERT_STATES else [(1200, 150)]
    for freq, ms in pattern:
        winsound.Beep(freq, ms)


def on_reading(address, name, rssi, info):
    now = time.time()
    with lock:
        prev = devices.get(address)
        devices[address] = {"address": address, "name": name or address, "rssi": rssi,
                            "last_seen": now, **info}
    changed = prev is None or prev["state"] != info["state"] or prev["events"] != info["events"]
    if not changed:
        return
    old = prev["state"] if prev else "-"
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {name}: {old} -> {info['state']}  events={info['events']} "
          f"peak={info['peak_g']:.1f} g  rssi={rssi} dBm")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.now().isoformat(timespec="seconds"), "device": name,
                            "address": address, "from": old, "to": info["state"],
                            "events": info["events"], "peak_g": info["peak_g"], "rssi": rssi}) + "\n")
    if prev is not None and info["state"] != "NORMAL":
        threading.Thread(target=beep, args=(info["state"],), daemon=True).start()


async def scan_ble():
    from bleak import BleakScanner

    def callback(device, adv):
        payload = adv.manufacturer_data.get(COMPANY_ID)
        if payload is None:
            return
        info = decode(payload)
        if info:
            on_reading(device.address, adv.local_name or device.name, adv.rssi, info)

    async with BleakScanner(detection_callback=callback):
        print("Scanning for GuardianBand advertisements... (Ctrl+C to stop)")
        while True:
            await asyncio.sleep(1)


async def simulate():
    """Fake device that walks through every state, for testing without hardware."""
    events, start = 0, time.time()
    script = [("NORMAL", 6), ("FALL_SUSPECTED", 5), ("NORMAL", 5), ("FALL_SUSPECTED", 4),
              ("FALL_CONFIRMED", 8), ("NORMAL", 5), ("SOS", 6)]
    codes = {v: k for k, v in STATES.items()}
    print("Demo mode: simulating GuardianBand_9B")
    while True:
        for state, seconds in script:
            if state != "NORMAL":  # PRD req 16: every alert transition counts
                events += 1
            peak = random.randint(28, 41)
            for _ in range(seconds * 2):
                uptime = int((time.time() - start) / 10)
                raw = bytes([PROTOCOL_VERSION, codes[state], events % 256, peak]) + uptime.to_bytes(2, "little")
                on_reading("A4:CF:12:34:56:9B", "GuardianBand_9B", random.randint(-70, -50), decode(raw))
                await asyncio.sleep(0.5)


PAGE = (HERE / "dashboard.html").read_text(encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            now = time.time()
            with lock:
                rows = [{**d, "online": now - d["last_seen"] < OFFLINE_AFTER_S,
                         "age_s": round(now - d["last_seen"], 1)} for d in devices.values()]
            incidents = []
            if LOG_PATH.exists():
                incidents = [json.loads(line) for line in
                             LOG_PATH.read_text(encoding="utf-8").splitlines()[-15:]][::-1]
            body, ctype = json.dumps({"devices": rows, "incidents": incidents}), "application/json"
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
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--demo", action="store_true", help="simulate a device instead of scanning BLE")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Dashboard: http://localhost:{args.port}   Incident log: {LOG_PATH}")
    try:
        asyncio.run(simulate() if args.demo else scan_ble())
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
