import os
import time
import uuid
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageStat
import imagehash

# --- SAFE GEMINI IMPORT ---
try:
    import google.generativeai as genai
except:
    genai = None

app = Flask(__name__)

# --- CONFIG ---
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# --- GEMINI SETUP ---
api_key = os.environ.get("GEMINI_API_KEY")

if genai and api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except:
        model = None
else:
    model = None

# --- MEMORY STORAGE ---
scan_history = []

# --- MOCK DATABASE ---
REFERENCE_DB = [
    {"id": "REF_001", "name": "Champions League Final", "hash": "8c3c3c3c3c3c3c3c"},
    {"id": "REF_002", "name": "NBA Finals", "hash": "f0f0f0f0f0f0f0f0"}
]

# --- MODIFICATION DETECTION ---
def analyze_modifications(img):
    stat = ImageStat.Stat(img)
    brightness = sum(stat.mean) / 3
    mods = []

    if brightness > 190:
        mods.append("Brightness High")
    elif brightness < 60:
        mods.append("Brightness Low")

    return mods if mods else ["None Detected"]

# --- SIMILARITY DETECTION ---
def get_similarity_data(user_hash_obj):
    top_match = {"sim": 0, "name": "Unknown"}

    for ref in REFERENCE_DB:
        ref_hash = imagehash.hex_to_hash(ref['hash'])
        distance = user_hash_obj - ref_hash
        similarity = max(0, (1 - (distance / 64.0)) * 100)

        if similarity > top_match['sim']:
            top_match = {
                "sim": round(similarity, 2),
                "name": ref['name']
            }

    return top_match

# --- SAFE AI FUNCTION ---
def get_ai_insight(sim, mods, asset_id):
    fallback = f"Asset {asset_id} shows {sim}% similarity. Mods: {', '.join(mods)}."

    if not model:
        return "[Fallback] " + fallback

    try:
        prompt = f"""
        You are a SportShield AI assistant.

        Analyze:
        Similarity: {sim}%
        Modifications: {mods}

        Give a short professional recommendation.
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except:
        return "[AI Error] " + fallback

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    start_perf = time.perf_counter()

    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "error": "No file uploaded",
            "matches": []
        }), 400

    file = request.files['file']

    try:
        # Save file
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process image
        img = Image.open(filepath).convert('RGB')
        u_hash = imagehash.phash(img)

        match = get_similarity_data(u_hash)
        mods = analyze_modifications(img)

        similarity = match['sim']

        # Risk scoring
        if similarity > 85:
            risk_level = "HIGH"
        elif similarity > 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        asset_id = f"SS-{uuid.uuid4().hex[:8].upper()}"
        ai_insight = get_ai_insight(similarity, mods, asset_id)

        # --- FIXED MATCHES ---
        matches = [
            {
                "source": "Instagram Fan Page",
                "sim": similarity,
                "type": mods[0] if mods else "Standard"
            },
            {
                "source": "Sports News Blog",
                "sim": round(similarity * 0.8, 1),
                "type": "Compressed"
            },
            {
                "source": "Twitter/X Feed",
                "sim": round(similarity * 0.6, 1),
                "type": "Resized"
            }
        ]

        result = {
            "success": True,
            "asset_id": asset_id,
            "hash": str(u_hash),
            "similarity": similarity,
            "risk_level": risk_level,
            "modifications": mods,
            "ai_insight": ai_insight,
            "image_url": f"/static/uploads/{filename}",
            "performance": f"{round(time.perf_counter() - start_perf, 3)}s",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "matches": matches
        }

        scan_history.append(result)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "matches": [],
            "ai_insight": "Analysis failed due to an internal error."
        }), 500

@app.route('/history')
def get_history():
    return jsonify(scan_history[::-1])

# --- RUN ---
if __name__ == '__main__':
    app.run(debug=True)