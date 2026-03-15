document.addEventListener("DOMContentLoaded", async () => {
    // Theme setup
    const themeBtn = document.getElementById("theme-toggle");
    const currentTheme = localStorage.getItem("theme") || "dark";
    document.body.setAttribute("data-theme", currentTheme);
    themeBtn.textContent = currentTheme === "dark" ? "☀️" : "🌙";

    themeBtn.addEventListener("click", () => {
        const newTheme = document.body.getAttribute("data-theme") === "dark" ? "light" : "dark";
        document.body.setAttribute("data-theme", newTheme);
        localStorage.setItem("theme", newTheme);
        themeBtn.textContent = newTheme === "dark" ? "☀️" : "🌙";
    });

    const fileInput = document.getElementById("file-input");
    const uploadBtn = document.getElementById("upload-btn");
    const fileText = document.getElementById("file-upload-text");
    const statusText = document.getElementById("upload-status");
    const errorText = document.getElementById("upload-error");

    let selectedFile = null;

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileText.textContent = selectedFile.name;
            uploadBtn.style.display = "inline-block";
        }
    });

    uploadBtn.addEventListener("click", async () => {
        if (!selectedFile) return;
        statusText.style.display = "block";
        uploadBtn.disabled = true;
        errorText.style.display = "none";

        try {
            // Save to localforage
            const recent = await localforage.getItem("recent_presentations") || [];
            // filter out if same name to avoid duplicates
            const filtered = recent.filter(r => r.name !== selectedFile.name);
            filtered.push({
                name: selectedFile.name,
                blob: selectedFile,
                date: new Date().toISOString()
            });
            if (filtered.length > 3) filtered.shift();
            await localforage.setItem("recent_presentations", filtered);

            await uploadFile(selectedFile);
        } catch (err) {
            statusText.style.display = "none";
            uploadBtn.disabled = false;
            errorText.textContent = err.message;
            errorText.style.display = "block";
        }
    });

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append("file", file);
        
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });
        
        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || "Upload failed");
        }
        
        const data = await res.json();
        window.location.href = `/present/${data.presentation_id}?token=${data.presenter_token}`;
    }

    // Load recent presentations via LocalForage
    const recentList = document.getElementById("recent-list");
    const recent = await localforage.getItem("recent_presentations") || [];
    
    if (recent.length === 0) {
        recentList.innerHTML += "<p style='color: var(--text-color); opacity: 0.6;'>No recent presentations.</p>";
    } else {
        // Reverse to show newest first
        [...recent].reverse().forEach((item) => {
            const div = document.createElement("div");
            div.className = "recent-item";
            const dateStr = new Date(item.date).toLocaleDateString();
            div.innerHTML = `<span><strong>${item.name}</strong> <small>(${dateStr})</small></span> <span>▶</span>`;
            div.addEventListener("click", async () => {
                try {
                    statusText.style.display = "block";
                    errorText.style.display = "none";
                    await uploadFile(item.blob);
                } catch(err) {
                    errorText.textContent = "Error loading previous presentation: " + err.message;
                    errorText.style.display = "block";
                    statusText.style.display = "none";
                }
            });
            recentList.appendChild(div);
        });
    }
});
