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

        // Visual Feedback
        document.getElementById('upload-progress').classList.remove('hidden');
        document.getElementById('upload-progress').style.width = '50%';
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                alert(data.error);
                return;
            }

            // Update UI
            resultsPanel.classList.remove('hidden');
            document.getElementById('res-img').src = data.image_url;
            document.getElementById('stat-perf').innerText = data.performance;
            document.getElementById('stat-risk').innerText = data.risk_level;
            document.getElementById('stat-risk').className = `text-2xl font-bold ${getRiskClass(data.risk_level)}`;
            document.getElementById('stat-sim').innerText = data.similarity + '%';
            document.getElementById('res-match-score').innerText = data.similarity + '% Match';
            document.getElementById('res-ai').innerText = data.ai_insight;
            document.getElementById('res-id').innerText = data.asset_id;

            // Populate Matches
            const matchList = document.getElementById('match-list');
            matchList.innerHTML = data.matches.map(m => `
                <div class="flex justify-between items-center p-4 bg-[#f8e5e5] rounded-xl">
                    <div>
                        <p class="font-bold text-sm">${m.source}</p>
                        <p class="text-[10px] text-[#c39ea0] font-bold uppercase">${m.type}</p>
                    </div>
                    <span class="font-mono font-bold text-[#fa255e]">${m.sim}%</span>
                </div>
            `).join('');

            // Reset progress
            document.getElementById('upload-progress').style.width = '100%';
            setTimeout(() => {
                document.getElementById('upload-progress').classList.add('hidden');
                document.getElementById('upload-progress').style.width = '0%';
            }, 1000);

            // Refresh History
            fetchHistory();
            
            // Scroll to results
            resultsPanel.scrollIntoView({ behavior: 'smooth' });

        } catch (err) {
            console.error("Analysis failed", err);
            alert("Upload failed. Check console.");
        }
    }

    async function fetchHistory() {
        const res = await fetch('/history');
        const data = await res.json();
        const container = document.getElementById('history-container');
        
        container.innerHTML = data.map(item => `
            <div class="history-card bg-white/50 p-4 rounded-xl border border-[#c39ea0]/20 flex items-center gap-4">
                <img src="${item.image_url}" class="w-12 h-12 rounded object-cover">
                <div class="flex-1">
                    <p class="text-[10px] font-bold text-[#c39ea0]">${item.timestamp}</p>
                    <p class="text-sm font-bold">${item.asset_id}</p>
                </div>
                <div class="text-right">
                    <p class="text-xs font-bold ${getRiskClass(item.risk_level)}">${item.similarity}%</p>
                </div>
            </div>
        `).join('');
    }

    function getRiskClass(lvl) {
        if (lvl === 'HIGH') return 'risk-high';
        if (lvl === 'MEDIUM') return 'risk-med';
        return 'risk-low';
    }

    // Initial Load
    fetchHistory();
});