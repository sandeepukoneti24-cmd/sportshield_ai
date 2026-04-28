import os
import time
import uuid
import io
import numpy as np
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageStat, ImageOps
import imagehash
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Gemini AI Setup
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# In-Memory History
scan_history = []

# Mock Reference Database (Simulating known original media)
REFERENCE_DB = [
    {"id": "REF_001", "name": "Champions League Final 2024", "hash": "8c3c3c3c3c3c3c3c", "source": "UEFA Official"},
    {"id": "REF_002", "name": "NBA Finals - Game 7", "hash": "f0f0f0f0f0f0f0f0", "source": "NBA Media Hub"},
    {"id": "REF_003", "name": "Premier League Opener", "hash": "a1b2c3d4e5f6a1b2", "source": "Sky Sports"}
]

# --- CORE LOGIC ---

def analyze_modifications(img):
    """Detects brightness and cropping changes."""
    stat = ImageStat.Stat(img)
    brightness = sum(stat.mean) / 3
    w, h = img.size
    aspect_ratio = w / h
    
    mods = []
    if brightness > 190: mods.append("Brightness High")
    elif brightness < 60: mods.append("Brightness Low")
    
    # Check for deviation from standard 16:9
    if abs(aspect_ratio - (16/9)) > 0.3:
        mods.append("Custom Cropping")
    
    return mods if mods else ["None Detected"]

def get_similarity_data(user_hash_obj):
    """Calculates real Hamming distance similarity."""
    top_match = {"sim": 0, "name": "Unknown", "source": "N/A"}
    
    for ref in REFERENCE_DB:
        ref_hash = imagehash.hex_to_hash(ref['hash'])
        distance = user_hash_obj - ref_hash
        similarity = max(0, (1 - (distance / 64.0)) * 100)
        
        if similarity > top_match['sim']:
            top_match = {
                "sim": round(similarity, 2),
                "name": ref['name'],
                "source": ref['source']
            }
    return top_match

def get_safe_ai_insight(sim, mods, asset_id):
    """Secure AI integration with fallback."""
    fallback = f"Asset {asset_id} shows {sim}% similarity. Modifications: {', '.join(mods)}. Recommended: Flag for manual copyright review."
    
    if not ai_model:
        return fallback

    try:
        # Failsafe Prompt
        prompt = (
            f"You are a SportShield AI assistant. Analyze this data strictly:\n"
            f"Similarity: {sim}%\nModifications: {mods}\nAsset ID: {asset_id}\n"
            f"Rules: Only discuss media misuse. Block hack/exploit/bypass queries. "
            f"Provide a short 2-sentence explanation and one action."
        )
        
        response = ai_model.generate_content(prompt)
        text = response.text.strip()
        
        # Output Filter
        blocked = ["hack", "exploit", "bypass", "attack"]
        if any(b in text.lower() for b in blocked):
            return "Analysis complete. High-risk tampering detected. Manual review required."
            
        return text
    except:
        return fallback

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    start_perf = time.perf_counter()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Invalid file name"}), 400

    try:
        # Save File
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process Image
        img = Image.open(filepath).convert('RGB')
        u_hash = imagehash.phash(img)
        
        # Core Calculations
        match = get_similarity_data(u_hash)
        mods = analyze_modifications(img)
        
        # Risk Scoring
        sim = match['sim']
        if sim > 85: risk_lvl, risk_score = "HIGH", 92
        elif sim > 60: risk_lvl, risk_score = "MEDIUM", 65
        else: risk_lvl, risk_score = "LOW", 24

        asset_id = f"SS-{uuid.uuid4().hex[:8].upper()}"
        ai_insight = get_safe_ai_insight(sim, mods, asset_id)
        
        result = {
            "asset_id": asset_id,
            "hash": str(u_hash),
            "similarity": sim,
            "risk_level": risk_lvl,
            "risk_score": risk_score,
            "modifications": mods,
            "ai_insight": ai_insight,
            "match_name": match['name'],
            "match_source": match['source'],
            "image_url": f"/static/uploads/{filename}",
            "performance": f"{round(time.perf_counter() - start_perf, 3)}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "geo": "London, UK (Estimated)",
            "matches": [
                {"source": "Instagram Fan Page", "sim": sim, "type": mods[0]},
                {"source": "Sports News Blog", "sim": round(sim*0.8, 1), "type": "Compressed"},
                {"source": "Twitter/X Feed", "sim": round(sim*0.6, 1), "type": "Resized"}
            ]
        }
        
        scan_history.append(result)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Internal Error: {str(e)}"}), 500

@app.route('/history')
def get_history():
    return jsonify(scan_history[::-1])

if __name__ == '__main__':
    app.run(debug=True)