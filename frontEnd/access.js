// access.js

function getClientId() {
    let id = localStorage.getItem("client_id");
    if (!id) {
        id = "user-" + Math.random().toString(36).slice(2);
        localStorage.setItem("client_id", id);
    }
    return id;
}

// expose globally so draw.js can use it
window.clientId = getClientId();

async function claimControl() {
    const res = await fetch("/api/claim", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: window.clientId })
    });

    const data = await res.json();
    console.log("[claim] server response:", data);

    if (!data.ok) {
        alert("Error claiming control: " + (data.error || "unknown"));
        window.location.href = "/waiting.html";
        return;
    }

    if (data.granted === true) {
        console.log("We ARE the active controller 👍");
        // we stay on index.html
    } else {
        console.log("We are NOT the controller, redirecting to waiting room.");
        window.location.href = "/waiting.html";
    }
}

async function heartbeat() {
    try {
        const res = await fetch("/api/heartbeat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_id: window.clientId })
        });
        const data = await res.json();
        // this updates last_seen on the server so we don't time out
        // not strictly required to do anything with 'data' here
        // but it's handy for debugging
        console.log("[heartbeat]", data);
    } catch (err) {
        console.warn("heartbeat failed:", err);
    }
}

// 1. claim immediately on load
claimControl();

// 2. send a heartbeat every 5 seconds to prove we're still here
setInterval(heartbeat, 5000);

// (still no beforeunload auto-release; timeout handles stale owners)
