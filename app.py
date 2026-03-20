from flask import Flask, render_template, request, jsonify
from pathlib import Path
import joblib
from utils.features import extract_features
from utils.verdict import compute_verdict
from utils.instagram_fetch import fetch_instagram_profile

app = Flask(__name__, template_folder='templates', static_folder='static')

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model" / "account_model.pkl"

# Load model at startup
try:
    data = joblib.load(MODEL_PATH)
    # The serialized artifact stores both model object and the training column order.
    MODEL = data["model"]
    FEATURE_COLUMNS = data["feature_columns"]
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    MODEL = None
    FEATURE_COLUMNS = []


# Serve the main HTML page
@app.route('/')
def index():
    return render_template('index.html')


# API: Analyze account
@app.route('/api/analyze', methods=['POST'])
def analyze_account():
    """Analyze account and return prediction"""
    try:
        data = request.get_json()
        
        # Extract features from input
        features = extract_features(
            username=data.get('username', ''),
            bio=data.get('bio', ''),
            followers_count=int(data.get('followers_count', 0)),
            following_count=int(data.get('following_count', 0)),
            media_count=int(data.get('media_count', 0)),
            has_profile_pic=int(data.get('has_profile_pic', 0)),
        )
        
        # Make prediction
        vector = [features[col] for col in FEATURE_COLUMNS]
        # predict_proba()[1] is probability of the "Fake" class.
        probability = float(MODEL.predict_proba([vector])[0][1])
        prediction = "Fake" if probability >= 0.5 else "Real"
        
        # Compute verdict
        verdict_result = compute_verdict(
            account_prediction=prediction,
            account_confidence=probability,
        )
        
        return jsonify({
            "success": True,
            "prediction": prediction,
            "confidence": round(probability, 4),
            "verdict": verdict_result.verdict,
            "risk_score": verdict_result.risk_score,
            "reasoning": verdict_result.reasoning,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# API: Fetch Instagram profile
@app.route('/api/fetch-instagram', methods=['POST'])
def fetch_instagram():
    """Fetch profile data from Instagram using Playwright"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        headless = data.get('headless', True)
        
        if not username:
            return jsonify({"success": False, "error": "Username required"}), 400
        
        profile, error = fetch_instagram_profile(
                username,
                session_id=data.get('session_id'),
                headless=headless,
            )
        
        if profile is None:
            return jsonify({
                "success": False,
                "error": error or "Could not fetch Instagram profile. Profile may be private or not exist."
            }), 400
        
        profile_dict = profile.to_dict()
        # Keep a numeric flag for the form select control in the UI.
        profile_dict['has_profile_pic'] = 1 if profile_dict.get('profile_pic_url') else 0
        
        return jsonify({
            "success": True,
            "profile": profile_dict,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    app.run(debug=False, port=5000, threaded=True)
