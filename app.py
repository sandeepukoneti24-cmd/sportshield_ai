import os
import time
import uuid
import io
import functools
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from PIL import Image, ImageStat
import imagehash

# AI Integration
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "sportshield_super_secret_123")

# --- CONFIGURATION ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", None)
SAFE_SYSTEM_PROMPT = """
You are a SportShield AI assistant. You ONLY analyze image similarity and media misuse.
Reject unrelated queries. Respond concisely. No hacking/coding talk.
"""

if HAS_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    ai_model = None

# In-Memory Storage (Resets on restart)
scan_history = []

# --- SECURITY UTILS ---

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Unauthorized. Please login."}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_ai_insight(similarity, mods, asset_id):
    """Secure AI integration with strict fallback and output filtering."""
    if not ai_model:
        return f"Asset {asset_id}: {similarity}% match with {mods[0]}. High probability of infringement. Action: Review for Takedown."

    try:
        # Strict prompt construction - No user input allowed here
        structured_prompt = f"{SAFE_SYSTEM_PROMPT}\nAnalyze: Similarity {similarity}%, Modifications: {mods}. Recommendation?"
        
        response = ai_model.generate_content(structured_prompt)
        text = response.text.strip()

        # Output Filter
        blocked_words = ["hack", "exploit", "bypass", "attack", "script"]
        if any(word in text.lower() for word in blocked_words):
            return "AI content flagged. Manual review required."
        
        return text[:250] # Limit length
    except:
        return "AI analysis unavailable. Standard protocol: Flag for manual review."

# --- AUTH ROUTES ---

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if data.get("username") == "admin" and data.get("password") == "admin123":
        session["user"] = "admin"
        return jsonify({"success": True})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('index'))

# --- CORE ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    start_time = time.perf_counter()
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    
    file = request.files['file']
    try:
        img = Image.open(io.BytesIO(file.read())).convert('RGB')
        current_hash = imagehash.phash(img)
        
        # Simulated Similarity Logic
        similarity = 92.4 # Demo value
        mods = ["Cropping Detected"] if img.width != img.height else ["Original Aspect"]
        
        asset_id = f"SS-{uuid.uuid4().hex[:8].upper()}"
        insight = get_ai_insight(similarity, mods, asset_id)
        
        result = {
            "asset_id": asset_id,
            "hash": str(current_hash),
            "similarity": similarity,
            "risk_level": "HIGH" if similarity > 80 else "LOW",
            "modifications": mods,
            "ai_insight": insight,
            "performance": f"{round(time.perf_counter() - start_time, 3)}s",
            "timestamp": time.strftime("%H:%M:%S")
        }
        
        # Save to History
        scan_history.append(result)
        if len(scan_history) > 10: scan_history.pop(0) # Keep last 10
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
@login_required
def get_history():
    return jsonify(scan_history[::-1]) # Return newest first

if __name__ == '__main__':
    app.run(debug=True)