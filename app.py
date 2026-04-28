import os
import time
import uuid
import io
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageStat
import imagehash

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Demo Reference Database (Original Assets)
REFERENCE_DB = [
    {"id": "REF_PL_001", "owner": "Premier League", "hash": "8c3c3c3c3c3c3c3c", "label": "Official Broadcast Feed"},
    {"id": "REF_NBA_002", "owner": "NBA Media", "hash": "f0f0f0f0f0f0f0f0", "label": "Courtside UHD Cam"},
]

def calculate_similarity(user_hash, ref_hash_hex):
    ref_hash = imagehash.hex_to_hash(ref_hash_hex)
    distance = user_hash - ref_hash
    return max(0, (1 - (distance / 64.0)) * 100)

def detect_tampering(img):
    mods = []
    stat = ImageStat.Stat(img)
    brightness = sum(stat.mean) / 3
    w, h = img.size
    
    if brightness > 210: mods.append("Brightness Filter")
    if brightness < 45: mods.append("Dark Overlay")
    if abs((w/h) - (16/9)) > 0.4: mods.append("Heavy Cropping")
    
    return mods if mods else ["No structural tampering detected"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    start_time = time.perf_counter()
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    img_bytes = file.read()
    
    try:
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        current_hash = imagehash.phash(img)
        
        # Match against DB
        best_match = {"sim": 0, "owner": "Unknown"}
        for ref in REFERENCE_DB:
            sim = calculate_similarity(current_hash, ref['hash'])
            if sim > best_match['sim']:
                best_match = {"sim": sim, "owner": ref['owner'], "label": ref['label']}

        mods = detect_tampering(img)
        
        # Risk Logic
        risk_score = int(best_match['sim'] * 0.85 + (15 if len(mods) > 0 else 0))
        risk_level = "HIGH" if risk_score > 75 else "MEDIUM" if risk_score > 40 else "LOW"

        return jsonify({
            "asset_id": f"SS-{uuid.uuid4().hex[:8].upper()}",
            "hash": str(current_hash),
            "similarity": round(best_match['sim'], 1),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "modifications": mods,
            "performance": f"{round(time.perf_counter() - start_time, 3)}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_insight": f"Detected {best_match['sim']}% overlap with {best_match['owner']} assets. {mods[0] if mods else ''} indicates intentional modification.",
            "matches": [
                {"source": "Fan Page (IG)", "sim": 94.2, "type": "Cropped", "risk": "High"},
                {"source": "News Blog", "sim": 81.5, "type": "Filtered", "risk": "Med"},
                {"source": "Twitter/X", "sim": 70.1, "type": "Original", "risk": "Low"}
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)