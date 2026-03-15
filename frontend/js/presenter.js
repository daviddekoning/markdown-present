document.addEventListener("DOMContentLoaded", async () => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const pathParts = window.location.pathname.split('/');
    const presentationId = pathParts[pathParts.length - 1];

    if (!token || !presentationId) {
        alert("Invalid URL");
        window.location.href = "/";
        return;
    }

    const shareUrl = `${window.location.origin}/view/${presentationId}`;
    const shareDiv = document.getElementById("share-url");
    shareDiv.textContent = shareUrl;
    shareDiv.addEventListener("click", () => {
        navigator.clipboard.writeText(shareUrl);
        const original = shareDiv.textContent;
        shareDiv.textContent = "Copied!";
        setTimeout(() => shareDiv.textContent = original, 2000);
    });

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
        if (!infoRes.ok) throw new Error("Presentation not found");
        const info = await infoRes.json();
        
        const mdRes = await fetch(`/api/presentations/${presentationId}/files/${info.main_markdown_path}`);
        if (!mdRes.ok) throw new Error("Failed to load markdown content");
        
        let mdText = await mdRes.text();
        
        // Rewrite asset paths, including plain HTML tags and markdown syntax
        mdText = mdText.replace(/!\[([^\]]*)\]\((?!http|data:)([^)]+)\)/g, `![$1](/api/presentations/${presentationId}/files/$2)`);
        mdText = mdText.replace(/src="(?!http|data:)([^"]+)"/g, `src="/api/presentations/${presentationId}/files/$1"`);
        
        document.getElementById("markdown-content").textContent = mdText;
    } catch(err) {
        alert(err.message);
        window.location.href = "/";
        return;
    }

    Reveal.initialize({
        controls: true,
        progress: true,
        history: false,
        center: true,
        transition: 'slide',
        plugins: [ RevealMarkdown ]
    });

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/present/${presentationId}?token=${token}`;
    const ws = new WebSocket(wsUrl);

    let isConnected = false;
    let sequenceNumber = 0;

    ws.onopen = () => {
        console.log("WebSocket connected");
        isConnected = true;
        setTimeout(() => syncState(), 500);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
        isConnected = false;
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.action === "ended") {
            window.location.href = "/";
        }
    };

    function syncState() {
        if(isConnected && ws.readyState === WebSocket.OPEN) {
            sequenceNumber++;
            ws.send(JSON.stringify({
                action: "change_slide",
                state: { ...Reveal.getIndices(), overview: Reveal.isOverview() },
                sequence: sequenceNumber,
                timestamp: Date.now()
            }));
        }
    }

    Reveal.on('slidechanged', syncState);
    Reveal.on('fragmentshown', syncState);
    Reveal.on('fragmenthidden', syncState);
    Reveal.on('overviewshown', syncState);
    Reveal.on('overviewhidden', syncState);

    document.getElementById("end-btn").addEventListener("click", async () => {
        if(confirm("End presentation for everyone?")) {
            await fetch(`/api/end/${presentationId}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ token: token })
            });
            window.location.href = "/";
        }
    });
});
