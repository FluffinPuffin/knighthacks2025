// controller.js

const forwardBtn = document.getElementById('forwardBtn');
const leftBtn = document.getElementById('leftBtn');
const rightBtn = document.getElementById('rightBtn');

// Store intervals for each button
let intervals = {};

// Function to "send" command continuously
function startSending(command) {
    if (!intervals[command]) {
        intervals[command] = setInterval(() => {
            console.log(command); // Replace this with your real send function
        }, 100); // send every 100ms
    }
}

function stopSending(command) {
    clearInterval(intervals[command]);
    intervals[command] = null;
}

// Helper to attach touch + mouse events
function attachButton(btn, command) {
    // Start sending on touchstart or mousedown
    btn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        startSending(command);
    });
    btn.addEventListener('mousedown', (e) => {
        e.preventDefault();
        startSending(command);
    });

    // Stop sending on touchend, touchcancel, mouseup, or mouseleave
    btn.addEventListener('touchend', () => stopSending(command));
    btn.addEventListener('touchcancel', () => stopSending(command));
    btn.addEventListener('mouseup', () => stopSending(command));
    btn.addEventListener('mouseleave', () => stopSending(command));
}

// Attach each button
// this puts in it the console log.
// find a way to send it to the robot later/chat gpt it
attachButton(forwardBtn, 'Move Forward');
attachButton(leftBtn, 'Turn Left');
attachButton(rightBtn, 'Turn Right');
