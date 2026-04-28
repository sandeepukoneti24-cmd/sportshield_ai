async function handleLogin() {
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;

    const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
    });

    if (res.ok) {
        document.getElementById('login-view').classList.add('hidden');
        document.getElementById('dashboard-view').classList.remove('hidden');
    } else {
        alert("Login Failed: Use admin / admin123");
    }
}

async function handleUpload(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/analyze', { method: 'POST', body: formData });
    if (res.status === 401) return alert("Session expired. Please login.");
    
    const data = await res.json();
    
    // Display results
    document.getElementById('results').classList.remove('hidden');
    document.getElementById('similarity-circle').innerText = data.similarity + "% Match";
    document.getElementById('ai-insight').innerText = data.ai_insight;
    document.getElementById('res-id').innerText = data.asset_id;
    document.getElementById('res-hash').innerText = data.hash;
}

async function loadHistory() {
    const res = await fetch('/history');
    const data = await res.json();
    const list = document.getElementById('history-list');
    
    document.getElementById('history-panel').classList.remove('hidden');
    list.innerHTML = data.map(item => `
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg border">
            <div>
                <p class="font-bold text-sm">${item.asset_id}</p>
                <p class="text-[10px] text-gray-400">${item.timestamp}</p>
            </div>
            <div class="text-right">
                <p class="text-sm font-bold ${item.risk_level === 'HIGH' ? 'text-red-600' : 'text-green-600'}">${item.similarity}%</p>
            </div>
        </div>
    `).join('');
}