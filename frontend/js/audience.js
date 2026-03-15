document.addEventListener("DOMContentLoaded", async () => {
    const pathParts = window.location.pathname.split('/');
    const presentationId = pathParts[pathParts.length - 1];

    if (!presentationId) {
        alert("Invalid URL");
        window.location.href = "/";
        return;
    }

    const themeBtn = document.getElementById("theme-toggle");
    const themeLink = document.getElementById("theme");
    const currentTheme = localStorage.getItem("theme") || "dark";
    document.body.setAttribute("data-theme", currentTheme);
    themeLink.href = `https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.4/theme/${currentTheme === "dark" ? "black" : "white"}.min.css`;
    themeBtn.textContent = currentTheme === "dark" ? "☀️" : "🌙";

    themeBtn.addEventListener("click", () => {
        const newTheme = document.body.getAttribute("data-theme") === "dark" ? "light" : "dark";
        document.body.setAttribute("data-theme", newTheme);
        themeLink.href = `https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.0.4/theme/${newTheme === "dark" ? "black" : "white"}.min.css`;
        localStorage.setItem("theme", newTheme);
        themeBtn.textContent = newTheme === "dark" ? "☀️" : "🌙";
    });

    try {
        const infoRes = await fetch(`/api/presentations/${presentationId}/info`);
        if (!infoRes.ok) throw new Error("Presentation not found or already ended.");
        const info = await infoRes.json();
        
        const mdRes = await fetch(`/api/presentations/${presentationId}/files/${info.main_markdown_path}`);
        if (!mdRes.ok) throw new Error("Failed to load markdown content");
        
        let mdText = await mdRes.text();
        mdText = mdText.replace(/!\[([^\]]*)\]\((?!http|data:)([^)]+)\)/g, `![$1](/api/presentations/${presentationId}/files/$2)`);
        mdText = mdText.replace(/src="(?!http|data:)([^"]+)"/g, `src="/api/presentations/${presentationId}/files/$1"`);
        
        document.getElementById("markdown-content").textContent = mdText;
    } catch(err) {
        alert(err.message);
        window.location.href = "/";
        return;
    }

    await Reveal.initialize({
        controls: false,
        controlsTutorial: false,
        progress: false,
        history: false,
        keyboard: false,
        touch: false,
        mouseWheel: false,
        help: false,
        overview: false,
        center: true,
        transition: 'slide',
        plugins: [ RevealMarkdown ]
    });

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/view/${presentationId}`;

    let ws = null;
    let lastSequence = -1;
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 10;
    let intentionallyClosed = false;

    function connectWebSocket() {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("WebSocket connected");
            reconnectAttempts = 0;
            document.getElementById("status-text").innerHTML = "<span style='color: #22c55e;'>●</span> Live";
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
            document.getElementById("status-text").innerHTML = "<span style='color: #ef4444;'>●</span> Disconnected";
            if (!intentionallyClosed && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                reconnectAttempts++;
                console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})...`);
                document.getElementById("status-text").innerHTML = "<span style='color: #f59e0b;'>●</span> Reconnecting...";
                setTimeout(connectWebSocket, delay);
            }
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.action === "ended") {
                intentionallyClosed = true;
                alert("Presentation ended by presenter.");
                window.location.href = "/";
            } else if (data.action === "slide_changed" && data.state) {
                // Guard against out-of-order packets via sequence checking
                if (data.sequence !== undefined) {
                    if (data.sequence <= lastSequence) {
                        console.log("Ignoring stale packet", data.sequence, "<=", lastSequence);
                        return; 
                    }
                    lastSequence = data.sequence;
                }

                const state = data.state;
                const h = state.h !== undefined ? state.h : state.indexh;
                const v = state.v !== undefined ? state.v : state.indexv;
                const f = state.f !== undefined ? state.f : state.indexf;
                Reveal.slide(h, v, f);
            }
        };
    }

    connectWebSocket();
});
