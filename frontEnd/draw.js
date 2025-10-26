// const canvas = document.getElementById('drawCanvas');
// const ctx = canvas.getContext('2d');
// const sendBtn = document.getElementById('sendBtn');
// const resetBtn = document.getElementById('resetBtn');

// let path = [];
// let startPoint = null;
// const scaleFactor = 72; // pixels per foot (adjust as needed)

// // --- Handle clicks to draw straight lines ---
// canvas.addEventListener('click', (e) => {
//     const rect = canvas.getBoundingClientRect();
//     const x = e.clientX - rect.left;
//     const y = e.clientY - rect.top;

//     if (!startPoint) {
//         startPoint = { x, y };
//     } else {
//         // draw line from startPoint to current click
//         ctx.beginPath();
//         ctx.moveTo(startPoint.x, startPoint.y);
//         ctx.lineTo(x, y);
//         ctx.stroke();

//         // save both points in path
//         path.push(startPoint);
//         path.push({ x, y });

//         startPoint = null; // reset for next line
//     }
// });

// // --- Convert path to distances & angles ---
// function calculateDistances(path) {
//     let distances = [];
//     for (let i = 1; i < path.length; i += 2) { // every pair of points
//         const start = path[i-1];
//         const end = path[i];
//         const dx = end.x - start.x;
//         const dy = end.y - start.y;
//         const dist = Math.sqrt(dx*dx + dy*dy);
//         const angle = Math.atan2(dy, dx); // radians
//         distances.push({
//             start,
//             end,
//             dist,
//             angle,
//             scaledDist: dist / scaleFactor
//         });
//     }
//     return distances;
// }

// // --- Send path data to console ---
// let storedPaths = []; // this can live globally

// sendBtn.addEventListener('click', () => {
//     if (path.length < 2) {
//         alert('Draw at least one line first!');
//         return;
//     }

//     const robotPath = calculateDistances(path);

//     console.log('--- Straight Line Path Data ---');
//     robotPath.forEach((step, index) => {
//         console.log(`Line ${index + 1}:`);
//         console.log(`  Start: (${step.start.x.toFixed(1)}, ${step.start.y.toFixed(1)})`);
//         console.log(`  End:   (${step.end.x.toFixed(1)}, ${step.end.y.toFixed(1)})`);
//         console.log(`  Distance (pixels): ${step.dist.toFixed(2)}`);
//         console.log(`  Distance (scaled): ${step.scaledDist.toFixed(2)} units`);
//         console.log(`  Angle (radians): ${step.angle.toFixed(2)}`);
//         console.log(`  Angle (degrees): ${(step.angle * 180 / Math.PI).toFixed(2)}`);
//     });

//     // Store data in an array for later use
//     storedPaths.push(robotPath);
//     // console.log(storedPaths);
//     //console.log('✅ Path saved! All stored paths:', storedPaths);
// });


// // --- Reset drawing ---
// resetBtn.addEventListener('click', () => {
//     ctx.clearRect(0, 0, canvas.width, canvas.height);
//     path = [];
//     startPoint = null;
//     // alert('Drawing reset!');
// });


const canvas = document.getElementById('drawCanvas');
const ctx = canvas.getContext('2d');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');

let path = [];
const scaleFactor = 72; // pixels per foot
const LOGICAL_WIDTH = 600;
const LOGICAL_HEIGHT = 400;

// --- Setup canvas for high-DPI screens ---
function setupCanvas() {
    const dpr = window.devicePixelRatio || 1;

    // Internal canvas size (logical drawing size)
    canvas.width = LOGICAL_WIDTH * dpr;
    canvas.height = LOGICAL_HEIGHT * dpr;

    // CSS size
    canvas.style.width = LOGICAL_WIDTH + "px";
    canvas.style.height = LOGICAL_HEIGHT + "px";

    // Scale context for drawing
    ctx.resetTransform?.(); // for modern browsers
    ctx.scale(dpr, dpr);

    redrawPath();
}
setupCanvas();
window.addEventListener('resize', setupCanvas);

// --- Redraw existing path ---
function redrawPath() {
    ctx.clearRect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT);

    for (let i = 0; i < path.length; i++) {
        const point = path[i];

        // Draw dot
        ctx.fillStyle = 'white';
        ctx.beginPath();
        ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
        ctx.fill();

        // Draw line to previous point
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

// --- Handle clicks to draw connected lines ---
// canvas.addEventListener('click', (e) => {
//     const rect = canvas.getBoundingClientRect();

//     // Convert click coordinates to canvas internal coordinates
//     const x = ((e.clientX - rect.left) / rect.width) * LOGICAL_WIDTH;
//     const y = ((e.clientY - rect.top) / rect.height) * LOGICAL_HEIGHT;

//     path.push({ x, y });
//     redrawPath();
// });

function getCanvasCoords(e) {
    const rect = canvas.getBoundingClientRect();
    let clientX, clientY;

    if (e.touches) {
        // touch event
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    } else {
        // mouse event
        clientX = e.clientX;
        clientY = e.clientY;
    }

    const x = ((clientX - rect.left) / rect.width) * LOGICAL_WIDTH;
    const y = ((clientY - rect.top) / rect.height) * LOGICAL_HEIGHT;
    return { x, y };
}

// --- Unified handler for clicks/touches ---
function addPoint(e) {
    e.preventDefault(); // prevent scrolling on touch
    const point = getCanvasCoords(e);
    path.push(point);
    redrawPath();
}

// --- Attach listeners ---
canvas.addEventListener('click', addPoint);
canvas.addEventListener('touchstart', addPoint);


// --- Convert path to distances & angles ---
function calculateDistances(path) {
    let distances = [];
    for (let i = 1; i < path.length; i++) {
        const start = path[i - 1];
        const end = path[i];
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const angle = Math.atan2(dy, dx);
        distances.push({
            start,
            end,
            dist,
            angle,
            scaledDist: dist / scaleFactor,
        });
    }
    return distances;
}

// --- Send path data to console ---
let storedPaths = [];
sendBtn.addEventListener('click', () => {
    if (path.length < 2) {
        alert('Draw at least two points first!');
        return;
    }

    const robotPath = calculateDistances(path);

    console.log('--- Auto-connected Path Data ---');
    robotPath.forEach((step, index) => {
        console.log(`Line ${index + 1}:`);
        console.log(`  Start: (${step.start.x.toFixed(1)}, ${step.start.y.toFixed(1)})`);
        console.log(`  End:   (${step.end.x.toFixed(1)}, ${step.end.y.toFixed(1)})`);
        console.log(`  Distance (pixels): ${step.dist.toFixed(2)}`);
        console.log(`  Distance (scaled): ${step.scaledDist.toFixed(2)} units`);
        console.log(`  Angle (radians): ${step.angle.toFixed(2)}`);
        console.log(`  Angle (degrees): ${(step.angle * 180 / Math.PI).toFixed(2)}`);
    });

    // Puts it into an array.
    storedPaths.push(robotPath);

    // Stringify the array of paths for easy copying.
    // you will need to unstrignify it later to use it.
    // const pathJSON = JSON.stringify(storedPaths);
    // console.log(pathJSON);

    // you might also want to just chat gpt it



});

// --- Reset drawing ---
resetBtn.addEventListener('click', () => {
    path = [];
    redrawPath();
});

