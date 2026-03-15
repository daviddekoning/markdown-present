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

    Reveal.initialize({
        controls: false,
        progress: false,
        history: false,
        keyboard: false,
        touch: false,
        center: true,
        transition: 'slide',
        plugins: [ RevealMarkdown ]
    });

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/view/${presentationId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log("WebSocket connected");
        document.getElementById("status-text").innerHTML = "<span style='color: #22c55e;'>●</span> Live";
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
        document.getElementById("status-text").innerHTML = "<span style='color: #ef4444;'>●</span> Disconnected";
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.action === "ended") {
            alert("Presentation ended by presenter.");
            window.location.href = "/";
        } else if (data.action === "slide_changed" && data.state) {
            const state = data.state;
            // Reveal.getIndices() returns {h: 0, v: 0, f: 0} or {indexh: 0, indexv: 0, indexf: 0}
            const h = state.h !== undefined ? state.h : state.indexh;
            const v = state.v !== undefined ? state.v : state.indexv;
            const f = state.f !== undefined ? state.f : state.indexf;
            Reveal.slide(h, v, f);
            
            // Handle overview mode sync if present
            if (state.overview !== undefined) {
                if (state.overview && !Reveal.isOverview()) {
                    Reveal.toggleOverview();
                } else if (!state.overview && Reveal.isOverview()) {
                    Reveal.toggleOverview();
                }
            }
        }
    };
});
