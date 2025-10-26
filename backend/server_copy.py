import time
import serial
from flask import Flask, request, jsonify, send_from_directory
import uuid 

# === CONFIG ===
# UI_DIR = "/home/dylanfc/robot-ui"
UI_DIR = "/home/dylanfc/robot-ui-original"

# Calibration placeholders (tune these later)
MS_PER_DEGREE = 10.0     # ms to rotate 1 degree
MS_PER_FOOT   = 1000.0   # ms to drive 1 foot

HEADING_OFFSET = 90.0 

# Arduino serial config (UPDATED BAUD)
ARDUINO_PORT = "/dev/ttyACM0"
BAUD = 115200

# Access control
is_busy = False
current_owner = None
queue = []  # user_ids waiting

OWNER_TIMEOUT = 5  # seconds without heartbeat before we consider owner gone
last_seen = {}  


app = Flask(
    __name__,
    static_folder=UI_DIR,
    static_url_path=""
)

def enqueue_if_needed(client_id):
    global queue
    if client_id not in queue:
        queue.append(client_id)


def mark_alive(client_id):
    """Record that this client_id is still active right now."""
    last_seen[client_id] = time.time()

def cleanup_owner_if_stale():
    """
    If the current owner hasn't heartbeated in OWNER_TIMEOUT seconds,
    drop them and promote whoever's next in queue.
    """
    global current_owner, queue

    if current_owner is None:
        return

    last = last_seen.get(current_owner, 0)
    if (time.time() - last) > OWNER_TIMEOUT:
        # current owner timed out -> promote next in queue or clear
        if queue:
            next_id = queue.pop(0)
            current_owner = next_id
            # make sure new owner has a timestamp so they don't get insta-dropped
            if next_id not in last_seen:
                last_seen[next_id] = time.time()
        else:
            current_owner = None

@app.route("/api/claim", methods=["POST"])
def claim():
    """
    Body: { "client_id": "some-id" }

    Behavior:
    - If no one owns the robot (or owner is stale), this client becomes current_owner.
    - If someone already owns it:
        - If it's this same client_id, return granted=true.
        - Otherwise, enqueue this client and return granted=false and their position.
    """
    global current_owner, queue

    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", None)
    if not client_id:
        return jsonify({"ok": False, "error": "no client_id"}), 400

    # this caller is alive
    mark_alive(client_id)

    # evict stale owner if needed
    cleanup_owner_if_stale()

    # Case 1: nobody owns it now
    if current_owner is None:
        current_owner = client_id
        return jsonify({
            "ok": True,
            "granted": True,
            "position": 0
        }), 200

    # Case 2: this client already is the owner
    if current_owner == client_id:
        return jsonify({
            "ok": True,
            "granted": True,
            "position": 0
        }), 200

    # Case 3: someone else owns it -> enqueue this client
    if client_id not in queue:
        queue.append(client_id)
    position = queue.index(client_id) + 1  # 1-based

    return jsonify({
        "ok": True,
        "granted": False,
        "position": position
    }), 200


@app.route("/api/release", methods=["POST"])
def release():
    """
    Body: { "client_id": "some-id" }

    Only the current owner can release.
    On release:
      - current_owner becomes next in queue, or None if queue empty
      - that next-in-line is popped from queue
    """
    global current_owner, queue

    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", None)
    if not client_id:
        return jsonify({"ok": False, "error": "no client_id"}), 400

    # only owner can release
    if current_owner != client_id:
        # not owner? nothing to do.
        return jsonify({"ok": True, "released": False, "owner": current_owner}), 200

    # owner is leaving, promote next queue entry (if any)
    if queue:
        next_id = queue.pop(0)
        current_owner = next_id
    else:
        current_owner = None

    return jsonify({
        "ok": True,
        "released": True,
        "owner": current_owner,
        "queue": queue
    }), 200

@app.route("/api/status", methods=["POST"])
def status():
    """
    Body: { "client_id": "some-id" }

    Returns:
      {
        "ok": true,
        "is_owner": bool,
        "position": int or null
      }

    Also performs stale-owner cleanup so waiting clients
    can auto-promote once the old owner disappears.
    """
    global current_owner, queue

    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", None)
    if not client_id:
        return jsonify({"ok": False, "error": "no client_id"}), 400

    # this caller is alive
    mark_alive(client_id)

    # maybe evict stale owner
    cleanup_owner_if_stale()

    if current_owner == client_id:
        return jsonify({
            "ok": True,
            "is_owner": True,
            "position": 0
        }), 200

    if client_id in queue:
        position = queue.index(client_id) + 1
        return jsonify({
            "ok": True,
            "is_owner": False,
            "position": position
        }), 200

    return jsonify({
        "ok": True,
        "is_owner": False,
        "position": None
    }), 200



@app.route("/api/heartbeat", methods=["POST"])
def heartbeat():
    """
    Body: { "client_id": "some-id" }

    We update that client's last_seen timestamp,
    clean up any stale owner,
    and report who the server currently thinks the owner is.
    """
    global current_owner

    data = request.get_json(silent=True) or {}
    client_id = data.get("client_id", None)
    if not client_id:
        return jsonify({"ok": False, "error": "no client_id"}), 400

    # mark this client as alive
    mark_alive(client_id)

    # see if we've got to evict a stale owner
    cleanup_owner_if_stale()

    return jsonify({
        "ok": True,
        "current_owner": current_owner
    }), 200

TURN_STEP_DEG = 10  # how much to rotate per nudge from LEFT/RIGHT

def send_manual_command_to_arduino(cmd):
    """
    Send one immediate command to the Arduino, respecting the new protocol.

    cmd can be:
      "FORWARD"  -> send '3' (fast forward)
      "STOP"     -> send '9'
      "LEFT"     -> send '5' then TURN_STEP_DEG
      "RIGHT"    -> send '4' then TURN_STEP_DEG

    Behavior matches the final Arduino sketch:
    - 3 sets both motors forward and leaves them running.
    - 9 stops both motors.
    - 4,<deg> turns right by <deg> using gyro, then stops and prints Done4.
    - 5,<deg> turns left  by <deg> using gyro, then stops and prints Done5.

    We open the serial port, send the burst, and read lines until we either
    see something that starts with "Done" or we time out.
    """

    serial_log = []

    # Map high-level cmd to one or two serial writes
    if cmd == "FORWARD":
        sequence = [1]  # just send 3\n
    elif cmd == "STOP":
        sequence = [9]  # just send 9\n
    elif cmd == "LEFT":
        sequence = [5, TURN_STEP_DEG]  # send 5\n then "10"\n
    elif cmd == "RIGHT":
        sequence = [4, TURN_STEP_DEG]  # send 4\n then "10"\n
    else:
        # Safety default: STOP
        sequence = [9]

    # Try to open the Arduino
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD, timeout=0.2)
        time.sleep(0.2)  # let Arduino settle
        hw_available = True
        serial_log.append(f"[info] opened {ARDUINO_PORT} @ {BAUD}")
    except Exception as e:
        hw_available = False
        ser = None
        serial_log.append(f"[warn] could not open {ARDUINO_PORT}: {e}")
        serial_log.append("[warn] SIM MODE (no Arduino)")

    # Helper: send one line
    def send_line(val):
        if hw_available:
            ser.write((str(val) + "\n").encode("utf-8"))
            ser.flush()
        serial_log.append(f"sent {val}")

    # Helper: read lines until "Done" or timeout
    def read_until_done(timeout_sec=2.0):
        if not hw_available:
            serial_log.append("arduino -> SIM_DONE")
            return
        end_t = time.time() + timeout_sec
        while time.time() < end_t:
            raw = ser.readline().decode("utf-8", errors="ignore").strip()
            if raw:
                serial_log.append(f"arduino -> {raw}")
                # Arduino ends turn with "Done4"/"Done5"
                # forward/stop say "Done3"/"Done9"
                if raw.startswith("Done"):
                    return
        serial_log.append("arduino -> (no final DONE)")

    # Send the whole sequence for this command
    for item in sequence:
        send_line(item)

    # Block/read for a short while so we can capture "Done#"
    read_until_done(timeout_sec=2.0)

    # Close serial if we actually opened it
    if hw_available and ser is not None:
        ser.close()
        serial_log.append("[info] closed serial")

    return serial_log




def build_motor_plan(segments):
    """
    Convert browser path segments into robot actions.

    Each segment from the browser is:
      { "distance_feet": <number>, "heading_degrees": <canvas-angle> }

    We:
    - turn robot to face the new heading
    - then drive forward that distance

    motor_plan will look like:
      [
        { "action": "TURN_RIGHT", "deg": 15.2 },
        { "action": "FORWARD", "distance_ft": 2.8 },
        ...
      ]

    NOTE: we are no longer storing "ms" for forward. We're storing "distance_ft".
    The Arduino will handle distance now using its IMU.
    """

    motor_plan = []
    current_heading = 0.0  # assume robot starts "facing north"

    for seg in segments:
        dist_ft = float(seg.get("distance_feet", 0.0))
        target_canvas = float(seg.get("heading_degrees", 0.0))

        # same heading math you had before:
        target_heading = target_canvas + HEADING_OFFSET
        while target_heading > 180.0:
            target_heading -= 360.0
        while target_heading < -180.0:
            target_heading += 360.0

        delta = target_heading - current_heading
        while delta > 180.0:
            delta -= 360.0
        while delta < -180.0:
            delta += 360.0

        # flip sign so robot turning matches canvas expectations
        delta = -delta

        turn_degrees = abs(delta)

        if turn_degrees > 0.5:
            if delta > 0:
                motor_plan.append({
                    "action": "TURN_LEFT",
                    "deg": turn_degrees
                })
            else:
                motor_plan.append({
                    "action": "TURN_RIGHT",
                    "deg": turn_degrees
                })

        if dist_ft > 0.01:
            motor_plan.append({
                "action": "FORWARD",
                "distance_ft": dist_ft
            })

        current_heading = target_heading

    return motor_plan

def run_motor_plan_on_arduino(motor_plan):
    """
    Execute the multi-step drawing plan on the Arduino with:
      - full boot sync
      - per-step resync
      - opcode/echo/param/Done handshake

    TURN_RIGHT:
        send 4
        wait echo "4"
        send <deg>
        wait "Done4"

    TURN_LEFT:
        send 5
        wait echo "5"
        send <deg>
        wait "Done5"

    FORWARD:
        send 3
        wait echo "3"
        send <distance_ft>
        wait "Done3"
    """

    serial_log = []

    # ---------- open serial (reboots Arduino) ----------
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD, timeout=0.2)
        hw_available = True
        serial_log.append(f"[info] opened {ARDUINO_PORT} @ {BAUD}")
    except Exception as e:
        hw_available = False
        ser = None
        serial_log.append(f"[warn] could not open {ARDUINO_PORT}: {e}")
        serial_log.append("[warn] SIM MODE (no Arduino)")

    # ---------- helpers ----------

    def read_line_now():
        if not hw_available:
            return None
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        return raw if raw else None

    def drain_and_log(seconds):
        """Read/log everything Arduino prints for N seconds."""
        if not hw_available:
            return
        end_t = time.time() + seconds
        while time.time() < end_t:
            raw = read_line_now()
            if raw:
                serial_log.append(f"arduino -> {raw}")

    def send_line(val):
        if hw_available:
            ser.write((str(val) + "\n").encode("utf-8"))
            ser.flush()
        serial_log.append(f"sent {val}")

    def wait_for_echo(expected_str, timeout_sec=2.0):
        """
        After we send an opcode (3,4,5), Arduino does:
            iput = Serial.parseInt();
            Serial.println(iput);
        We wait until we SEE that echo.
        """
        if not hw_available:
            serial_log.append("arduino -> (SIM echo ok)")
            return True
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            raw = read_line_now()
            if raw:
                serial_log.append(f"arduino -> {raw}")
                if raw.strip() == str(expected_str):
                    return True
        serial_log.append("arduino -> (no echo)")
        return False

    def wait_for_done(timeout_sec=15.0):
        """
        After sending full command (opcode + param),
        Arduino eventually prints Done3 / Done4 / Done5.
        We block until we see a line starting with "Done".
        """
        if not hw_available:
            serial_log.append("arduino -> SIM_DONE")
            return
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            raw = read_line_now()
            if raw:
                serial_log.append(f"arduino -> {raw}")
                if raw.startswith("Done"):
                    return
        serial_log.append("arduino -> (no final DONE)")

    def sync_ready():
        """
        IMPORTANT:
        After Arduino finishes a command (like a turn),
        it loops, dumps IMU lines, delay(200), clearInputBuffer(),
        THEN waits for the next command.

        If we blast the next opcode too early, it gets cleared.

        So before sending the NEXT command, we let that cycle finish,
        then drain any IMU spam so the RX buffer is clean.
        """
        if not hw_available:
            return
        time.sleep(0.5)   # give it time to print accel/gyro and clearInputBuffer
        drain_and_log(0.5)

    # ---------- 1. BOOT SYNC ----------
    if hw_available:
        # let Arduino boot + print "MPU6050 Found!" + first IMU spam
        time.sleep(3.5)
        drain_and_log(1.0)

    # ---------- 2. RUN EACH STEP ----------
    first_step = True
    for step in motor_plan:
        action = step["action"]

        # before sending ANYTHING after the first command,
        # resync so Arduino is waiting at "while(Serial.available()==0){}"
        if not first_step:
            sync_ready()
        first_step = False

        if action == "TURN_LEFT":
            deg_val = int(round(step.get("deg", 0)))
            if deg_val < 1:
                continue

            # handshake for left turn (opcode 5)
            send_line(5)
            wait_for_echo(5, timeout_sec=2.0)

            send_line(deg_val)
            wait_for_done(timeout_sec=15.0)

        elif action == "TURN_RIGHT":
            deg_val = int(round(step.get("deg", 0)))
            if deg_val < 1:
                continue

            # handshake for right turn (opcode 4)
            send_line(4)
            wait_for_echo(4, timeout_sec=2.0)

            send_line(deg_val)
            wait_for_done(timeout_sec=15.0)

        elif action == "FORWARD":
            dist_ft = float(step.get("distance_ft", 0.0))
            if dist_ft <= 0.0:
                continue

            # handshake for forward distance mode (opcode 1)
            send_line(1)
            wait_for_echo(1, timeout_sec=2.0)

            send_line(dist_ft)
            wait_for_done(timeout_sec=15.0)

        else:
            # fallback / emergency stop
            send_line(9)
            wait_for_echo(9, timeout_sec=2.0)
            wait_for_done(timeout_sec=3.0)

    # ---------- 3. CLOSE SERIAL ----------
    if hw_available and ser is not None:
        ser.close()
        serial_log.append("[info] closed serial")

    return serial_log




def send_manual_command_to_arduino(cmd):
    """
    Fire a single immediate command to the Arduino, or simulate if not plugged in.

    cmd is one of: "FORWARD", "LEFT", "RIGHT", "STOP"

    Arduino opcodes from your sketch:
      3 -> forward fast
      4 -> turn right
      5 -> turn left
      9 -> stop
    """

    serial_log = []

    # translate high-level cmd to opcode
    if cmd == "FORWARD":
        opcode = 1
    elif cmd == "LEFT":
        opcode = 5
    elif cmd == "RIGHT":
        opcode = 4
    elif cmd == "STOP":
        opcode = 9
    else:
        opcode = 9  # default = STOP for safety

    # try to open hardware
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD, timeout=1)
        time.sleep(0.2)  # tiny delay so the Arduino is ready
        hw_available = True
        serial_log.append(f"[info] opened {ARDUINO_PORT} @ {BAUD}")
    except Exception as e:
        # no Arduino plugged in? that's fine; simulate.
        hw_available = False
        ser = None
        serial_log.append(f"[warn] could not open {ARDUINO_PORT}: {e}")
        serial_log.append("[warn] SIM MODE (no Arduino)")

    # send the opcode
    def send_line(line):
        if hw_available:
            ser.write((str(line) + "\n").encode("utf-8"))
            ser.flush()
        serial_log.append(f"sent {line}")

    # read one reply line (non-blocking-ish)
    def read_reply():
        if not hw_available:
            serial_log.append("arduino -> SIM_DONE")
            return
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if raw:
            serial_log.append(f"arduino -> {raw}")

    send_line(opcode)
    read_reply()

    if hw_available and ser is not None:
        ser.close()
        serial_log.append("[info] closed serial")

    return serial_log


@app.route("/api/manualdrive", methods=["POST"])
def manualdrive():
    """
    Live driving endpoint for controller.html.
    Body:
    {
      "user_id": "<clientId from access.js>",
      "command": "FORWARD" | "LEFT" | "RIGHT" | "STOP"
    }

    Behavior:
    - Only the current_owner can actually drive.
    - If you're not the current_owner, we respond with status:"queued"
      so the frontend can throw you to waiting.html.
    """

    global current_owner, queue

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    command = data.get("command")

    if not user_id or not command:
        return jsonify({
            "ok": False,
            "error": "bad request"
        }), 400

    # If someone else is owner, you're not allowed to drive. You get queued.
    if current_owner is not None and current_owner != user_id:
        if user_id not in queue:
            queue.append(user_id)
        return jsonify({
            "ok": True,
            "status": "queued",
            "serial_log": []
        }), 200

    # You ARE the owner -> send the immediate command
    serial_log = send_manual_command_to_arduino(command)

    return jsonify({
        "ok": True,
        "status": "executed",
        "command": command,
        "serial_log": serial_log
    }), 200


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/api/runpath", methods=["POST"])
def runpath():
    """
    Browser calls this after drawing.
    Body:
    {
      "user_id": "web-user",
      "segments": [
        { "distance_feet": <num>, "heading_degrees": <num> },
        ...
      ]
    }

    Flow:
    1. Check if caller is allowed to drive (must match current_owner).
    2. If someone else owns it, return status:"queued".
    3. If we're already executing a plan (is_busy True), also return queued/busy.
    4. Otherwise:
         - build motor plan
         - run it on the Arduino
         - return motor_plan + serial_log
    """

    global current_owner, queue, is_busy

    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", None)
    segments = data.get("segments", [])

    if not user_id or not isinstance(segments, list):
        return jsonify({
            "ok": False,
            "error": "bad request"
        }), 400

    # 1. Only the current owner is allowed to actually drive the robot.
    # If you're not the owner, you get 'queued' so your browser should sit
    # on waiting.html.
    if current_owner is not None and current_owner != user_id:
        # make sure you're on the queue so you'll get promoted later
        if user_id not in queue:
            queue.append(user_id)

        return jsonify({
            "ok": True,
            "status": "queued",
            "queue": queue,
            "motor_plan": [],
            "serial_log": []
        }), 200

    # 2. If the robot is currently mid-run (already executing a previous plan),
    # don't start a second plan on top. Tell them it's still busy.
    if is_busy:
        # same response shape so the frontend treats this as "wait"
        return jsonify({
            "ok": True,
            "status": "queued",
            "queue": queue,
            "motor_plan": [],
            "serial_log": []
        }), 200

    # 3. We're allowed to run! Build the low-level motor plan.
    motor_plan = build_motor_plan(segments)

    # Mark busy so nobody else can interleave a run
    is_busy = True

    try:
        # Actually send the plan to the Arduino and capture the log
        serial_log = run_motor_plan_on_arduino(motor_plan)

    finally:
        # Always clear busy, even if something exploded talking to Arduino
        is_busy = False

    # 4. Return what happened back to the browser for debug display
    return jsonify({
        "ok": True,
        "status": "executed",
        "motor_plan": motor_plan,
        "serial_log": serial_log,
        "queue": queue
    }), 200


@app.route("/api/admin/state", methods=["GET"])
def admin_state():
    return jsonify({
        "is_busy": is_busy,
        "queue": queue
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
