document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const resultsPanel = document.getElementById('results-panel');

    // Click to upload
    dropZone.addEventListener('click', () => fileInput.click());

    // File selection
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files[0]);
    });

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#fa255e';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '#c39ea0';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        handleFiles(e.dataTransfer.files[0]);
    });

    async function handleFiles(file) {
        if (!file) return;

        const progressBar = document.getElementById('upload-progress');
        progressBar.classList.remove('hidden');
        progressBar.style.width = '40%';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            console.log("API RESPONSE:", data); // DEBUG

            if (!data.success) {
                alert(data.error || "Something went wrong");
                return;
            }

            // Show results panel
            resultsPanel.classList.remove('hidden');

            // Update main stats
            document.getElementById('res-img').src = data.image_url || '';
            document.getElementById('stat-perf').innerText = data.performance || '-';
            document.getElementById('stat-risk').innerText = data.risk_level || '-';
            document.getElementById('stat-risk').className =
                `text-2xl font-bold ${getRiskClass(data.risk_level)}`;

            document.getElementById('stat-sim').innerText =
                (data.similarity || 0) + '%';

            document.getElementById('res-match-score').innerText =
                (data.similarity || 0) + '% Match';

            document.getElementById('res-ai').innerText =
                data.ai_insight || "No AI insight available";

            document.getElementById('res-id').innerText =
                data.asset_id || '-';

            // 🏆 SAFE MATCHES RENDER
            const matchList = document.getElementById('match-list');

            if (matchList) {
                const safeMatches = data.matches || [];

                if (safeMatches.length > 0) {
                    matchList.innerHTML = safeMatches.map(m => `
                        <div class="flex justify-between items-center p-4 bg-[#f8e5e5] rounded-xl">
                            <div>
                                <p class="font-bold text-sm">${m.source || 'Unknown Source'}</p>
                                <p class="text-[10px] text-[#c39ea0] font-bold uppercase">${m.type || 'Standard'}</p>
                            </div>
                            <span class="font-mono font-bold text-[#fa255e]">${m.sim || 0}%</span>
                        </div>
                    `).join('');
                } else {
                    matchList.innerHTML = `
                        <p class="text-sm text-gray-400 p-4">
                            No secondary matches found.
                        </p>
                    `;
                }
            }

            // Progress complete
            progressBar.style.width = '100%';

            setTimeout(() => {
                progressBar.classList.add('hidden');
                progressBar.style.width = '0%';
            }, 800);

            // Refresh history
            fetchHistory();

            // Scroll
            resultsPanel.scrollIntoView({ behavior: 'smooth' });

        } catch (err) {
            console.error("Analysis failed", err);
            alert("Upload failed. Check console.");
        }
    }

    async function fetchHistory() {
        try {
            const res = await fetch('/history');
            const data = await res.json();

            const container = document.getElementById('history-container');

            if (!container) return;

            const safeHistory = data || [];

            if (safeHistory.length === 0) {
                container.innerHTML = `
                    <p class="text-sm text-gray-400">
                        No history yet.
                    </p>
                `;
                return;
            }

            container.innerHTML = safeHistory.map(item => `
                <div class="bg-white/50 p-4 rounded-xl border border-[#c39ea0]/20 flex items-center gap-4">
                    <img src="${item.image_url || ''}" class="w-12 h-12 rounded object-cover">
                    <div class="flex-1">
                        <p class="text-[10px] font-bold text-[#c39ea0]">
                            ${item.timestamp || ''}
                        </p>
                        <p class="text-sm font-bold">
                            ${item.asset_id || ''}
                        </p>
                    </div>
                    <div class="text-right">
                        <p class="text-xs font-bold ${getRiskClass(item.risk_level)}">
                            ${item.similarity || 0}%
                        </p>
                    </div>
                </div>
            `).join('');

        } catch (err) {
            console.error("History load failed", err);
        }
    }

    function getRiskClass(level) {
        if (level === 'HIGH') return 'text-[#fa255e]';
        if (level === 'MEDIUM') return 'text-[#c39ea0]';
        return 'text-green-500';
    }

    // Initial load
    fetchHistory();
});