document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    dropZone.onclick = () => fileInput.click();

    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Show UI Loading State
        const originalContent = dropZone.innerHTML;
        dropZone.innerHTML = `
            <div class="flex flex-col items-center justify-center">
                <div class="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p class="font-bold text-gray-900">Generating Digital Fingerprint...</p>
            </div>`;

        // Preview
        const reader = new FileReader();
        reader.onload = (event) => {
            document.getElementById('preview-img').src = event.target.result;
            document.getElementById('match-img').src = event.target.result;
        };
        reader.readAsDataURL(file);

        // API Call
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/analyze', { method: 'POST', body: formData });
            const data = await response.json();

            // Populate Results
            document.getElementById('results-area').classList.remove('hidden');
            document.getElementById('res-id').innerText = data.asset_id;
            document.getElementById('res-hash').innerText = data.hash;
            document.getElementById('res-perf').innerText = data.performance;
            document.getElementById('similarity-score').innerText = `${data.similarity}% Match`;
            document.getElementById('ai-insight').innerText = data.ai_insight;

            // Risk Level UI
            const pill = document.getElementById('risk-pill');
            const alert = document.getElementById('live-alert');
            pill.innerText = `${data.risk_level} Risk`;
            
            if (data.risk_level === 'HIGH') {
                pill.className = "px-4 py-1 rounded-full text-[10px] font-black uppercase bg-red-100 text-red-600";
                alert.classList.remove('hidden');
            } else {
                pill.className = "px-4 py-1 rounded-full text-[10px] font-black uppercase bg-green-100 text-green-600";
                alert.classList.add('hidden');
            }

            // Tags
            const tags = document.getElementById('mod-tags');
            tags.innerHTML = '';
            data.modifications.forEach(m => {
                tags.innerHTML += `<span class="bg-gray-100 text-gray-600 px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-tighter">${m}</span>`;
            });

            // Initialize Charts
            initCharts();

            // Smooth Scroll
            window.scrollTo({ top: 700, behavior: 'smooth' });

        } catch (err) {
            alert("Scan failed. Ensure backend is running.");
            console.error(err);
        } finally {
            dropZone.innerHTML = originalContent;
        }
    };
});

function initCharts() {
    const ctx1 = document.getElementById('trendsChart').getContext('2d');
    new Chart(ctx1, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Violations',
                data: [12, 19, 3, 5, 2, 3, 20],
                borderColor: '#2563EB',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(37, 99, 235, 0.05)'
            }]
        },
        options: { plugins: { legend: { display: false } }, scales: { y: { display: false }, x: { grid: { display: false } } } }
    });

    const ctx2 = document.getElementById('sourceChart').getContext('2d');
    new Chart(ctx2, {
        type: 'doughnut',
        data: {
            labels: ['Fan Pages', 'News', 'Blogs'],
            datasets: [{
                data: [65, 20, 15],
                backgroundColor: ['#2563EB', '#60A5FA', '#E2E8F0'],
                borderWidth: 0
            }]
        },
        options: { plugins: { legend: { position: 'bottom' } }, cutout: '70%' }
    });
}