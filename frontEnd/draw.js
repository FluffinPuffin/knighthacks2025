// draw.js
// handles drawing + sending path to Pi

// --- DOM refs ---
const canvas   = document.getElementById('drawCanvas');
const ctx      = canvas.getContext('2d');
const sendBtn  = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');

// drawing state
let path = [];

// calibration
// const scaleFactor    = 72;   // pixels per foot
const scaleFactor    = 35000; 
const LOGICAL_WIDTH  = 600;
const LOGICAL_HEIGHT = 400;

// Hi-DPI canvas setup
function setupCanvas() {
    const dpr = window.devicePixelRatio || 1;

    // internal buffer size
    canvas.width  = LOGICAL_WIDTH * dpr;
    canvas.height = LOGICAL_HEIGHT * dpr;

    // CSS display size
    canvas.style.width  = LOGICAL_WIDTH + "px";
    canvas.style.height = LOGICAL_HEIGHT + "px";

    // scale context so drawing math stays in "logical px"
    if (ctx.resetTransform) {
        ctx.resetTransform();
    }
    ctx.scale(dpr, dpr);

    redrawPath();
}

// Call once and re-run on resize
setupCanvas();
window.addEventListener('resize', setupCanvas);

// Redraw path (dots + lines)
function redrawPath() {
    ctx.clearRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);

    for (let i = 0; i < path.length; i++) {
        const point = path[i];

        // dot
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
        ctx.fill();

        // line from previous
        if (i > 0) {
            const prev = path[i - 1];
            ctx.strokeStyle = 'white';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(prev.x, prev.y);
            ctx.lineTo(point.x, point.y);
            ctx.stroke();
        }
    }
}

// Convert click/touch screen coords into logical canvas coords
function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    let clientX, clientY;

    if (e.touches && e.touches.length > 0) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    } else {
        clientX = e.clientX;
        clientY = e.clientY;
    }

    const x = ((clientX - rect.left) / rect.width) * LOGICAL_WIDTH;
    const y = ((clientY - rect.top)  / rect.height) * LOGICAL_HEIGHT;
    return { x, y };
}

// Add a point on click/touch
function addPoint(e) {
    e.preventDefault(); // stops page scrolling on touch
    const p = getCanvasCoords(e);
    path.push(p);
    redrawPath();
}

// Listener hookup
canvas.addEventListener('click', addPoint);
canvas.addEventListener('touchstart', addPoint);

// Build the "segments" array the Pi expects
// segments = [
//   { distance_feet: <number>, heading_degrees: <number> },
//   ...
// ]
function calculateDistances(pathArr) {
    const segments = [];
    for (let i = 1; i < pathArr.length; i++) {
        const start = pathArr[i - 1];
        const end   = pathArr[i];

        const dx = end.x - start.x;
        const dy = end.y - start.y;

        const dist_px = Math.sqrt(dx * dx + dy * dy);
        if (dist_px === 0) continue;

        var distance_feet = dist_px / scaleFactor;

        if (distance_feet < 0.01)
        {
            distance_feet = distance_feet + 0.005;
        } // skip tiny moves

        const angle_rad = Math.atan2(dy, dx);
        
        const angle_deg = angle_rad * 180 / Math.PI;
        
        const roundedString = distance_feet.toFixed(6);
        segments.push({
            distance_feet: roundedString,
            heading_degrees: angle_deg
        });
    }
    return segments;
}

// Send path to Pi
async function sendToPi() {
    if (path.length < 2) {
        alert('Draw at least two points first!');
        return;
    }

    // Build the movement segments
    const segments = calculateDistances(path);

    // IMPORTANT:
    // user_id MUST match the ID that access.js told the Pi via /api/claim
    // access.js stored that in window.clientId
    const payload = {
        user_id: window.clientId,
        segments: segments
    };

    console.log(">>> Sending payload to Pi /api/runpath");
    console.log(payload);

    try {
        const res = await fetch("/api/runpath", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        // If not the active owner OR robot still busy, server replies {status:"queued"}
        if (data.status === "queued") {
            console.log("Robot busy or you're not the owner yet. Redirecting...");
            console.log(data);
            window.location.href = "/waiting.html";
            return;
        }

        // Otherwise you'll see the motor_plan and serial_log
        console.log("<<< Pi response:");
        console.log(data);

    } catch (err) {
        console.error("!!! Error talking to Pi:", err);
    }
}

// Hook up buttons
sendBtn.addEventListener('click', sendToPi);

resetBtn.addEventListener('click', () => {
    path = [];
    redrawPath();
    console.log("Path cleared.");
});

// Draw once initially (in case setupCanvas ran before path had anything)
redrawPath();
