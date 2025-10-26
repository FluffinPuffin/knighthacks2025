function getClientId() {
    let id = localStorage.getItem("client_id");
    if (!id) {
        id = "user-" + Math.random().toString(36).slice(2);
        localStorage.setItem("client_id", id);
    }
    return id;
}

const clientId = getClientId();

async function pollStatus() {
    try {
        const res = await fetch("/api/status", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_id: clientId })
        });

        const data = await res.json();
        console.log("[status]", data);

        // If server says we're now the owner, go to draw page
        if (data.ok && data.is_owner === true) {
            console.log("It's our turn now, redirecting to index.html");
            window.location.href = "/index.html";
            return;
        }

        // Otherwise just keep waiting.
        // (Optional) you can show queue position:
        // data.position might be 1,2,3,... or null
        // console.log("Queue position:", data.position);

    } catch (err) {
        console.warn("pollStatus error:", err);
    }
}

// check immediately and also every 2s
pollStatus();
setInterval(pollStatus, 2000);
