from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
import joblib

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fake_news_classifier_model.joblib"
VECTORIZER_PATH = BASE_DIR / "tfidf_vectorizer.joblib"

# Load model and vectorizer from absolute paths so startup works from any cwd.
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

@app.route("/")
def home():
    return "Fake News API is running"

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json(silent=True) or {}
        text = str(data.get("text", "")).strip()

        if not text:
            return jsonify({"error": "text is required"}), 400

        # Convert text to numeric features, then classify.
        text_vectorized = vectorizer.transform([text])

        prediction = model.predict(text_vectorized)

        result = "fake" if prediction[0] == 0 else "real"

        return jsonify({"prediction": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)