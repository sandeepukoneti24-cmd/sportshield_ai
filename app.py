import os
import time
import uuid
import io
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageStat
import imagehash

# --- FIX 1: SAFE IMPORT ---
try:
    import google.generativeai as genai
except (ImportError, ModuleNotFoundError):
    genai = None

app = Flask(__name__)

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# --- FIX 2: SAFE INITIALIZATION ---
api_key = os.environ.get("GEMINI_API_KEY")
if genai and api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        model = None
else:
    model = None

# In-Memory History
scan_history = []

# Mock Reference Database
REFERENCE_DB = [
    {"id": "REF_001", "name": "Champions League Final", "hash": "8c3c3c3c3c3c3c3c"},
    {"id": "REF_002", "name": "NBA Finals", "hash": "f0f0f0f0f0f0f0f0"}
]

# --- CORE LOGIC ---

def analyze_modifications(img):
    stat = ImageStat.Stat(img)
    brightness = sum(stat.mean) / 3
    mods = []
    if brightness > 190: mods.append("Brightness High")
    elif brightness < 60: mods.append("Brightness Low")
    return mods if mods else ["None Detected"]

def get_similarity_data(user_hash_obj):
    top_match = {"sim": 0, "name": "Unknown"}
    for ref in REFERENCE_DB:
        ref_hash = imagehash.hex_to_hash(ref['hash'])
        distance = user_hash_obj - ref_hash
        similarity = max(0, (1 - (distance / 64.0)) * 100)
        if similarity > top_match['sim']:
            top_match = {"sim": round(similarity, 2), "name": ref['name']}
    return top_match

# --- FIX 3: SAFE AI FUNCTION ---
def get_ai_insight(sim, mods, asset_id):
    fallback_msg = f"Asset {asset_id} shows {sim}% match. Mods: {', '.join(mods)}. Action: Manual review required."
    
    if not model:
        return f"[Default Logic] {fallback_msg}"

    try:
        prompt = f"Analyze: Similarity {sim}%, Mods {mods}. Provide a 1-sentence recommendation."
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return f"[Fallback] {fallback_msg}"

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    start_perf = time.perf_counter()
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    try:
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        img = Image.open(filepath).convert('RGB')
        u_hash = imagehash.phash(img)
        match = get_similarity_data(u_hash)
        mods = analyze_modifications(img)
        
        asset_id = f"SS-{uuid.uuid4().hex[:8].upper()}"
        ai_insight = get_ai_insight(match['sim'], mods, asset_id)
        
        result = {
            "asset_id": asset_id,
            "hash": str(u_hash),
            "similarity": match['sim'],
            "risk_level": "HIGH" if match['sim'] > 85 else "LOW",
            "modifications": mods,
            "ai_insight": ai_insight,
            "image_url": f"/static/uploads/{filename}",
            "performance": f"{round(time.perf_counter() - start_perf, 3)}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        scan_history.append(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history')
def get_history():
    return jsonify(scan_history[::-1])

if __name__ == '__main__':
    app.run(debug=True)