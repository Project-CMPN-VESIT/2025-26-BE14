from flask import Flask, render_template, request
import joblib
import numpy as np
import pandas as pd
import re
from datetime import datetime

app = Flask(__name__)

# --- Load trained model and vectorizer ---
model = joblib.load('app/logistic_model.pkl')
vectorizer = joblib.load('app/vectorizer.pkl')

# --- Simulate stored frequencies (for demo); replace with your real stats if available ---
username_counts = {}
ip_counts = {}

# --- Cleaning function (same as training) ---
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# --- Compute time difference in minutes ---
def compute_time_diff_min(post_ts, review_ts):
    try:
        post_dt = pd.to_datetime(post_ts)
        review_dt = pd.to_datetime(review_ts)
        return (review_dt - post_dt).total_seconds() / 60.0
    except Exception:
        return 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # --- Collect inputs ---
    review_text = request.form.get('review_text', '')
    category = request.form.get('category', '')
    rating_raw = request.form.get('rating', '')
    username = request.form.get('username', '')
    post_timestamp = request.form.get('post_timestamp', '')
    review_timestamp = request.form.get('review_timestamp', '')

    ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', '')

    # --- Rule 1: Timestamp logic ---
    try:
        post_dt = pd.to_datetime(post_timestamp)
        review_dt = pd.to_datetime(review_timestamp)
        if review_dt < post_dt:
            result = "🚨 Fake Review (Review posted before product/post date)"
            return render_template('index.html', prediction=result)
    except Exception:
        pass

    # --- Rule 2: Repetitive/spam check ---
    words = review_text.lower().split()
    if len(words) > 4:
        repeated_ratio = (len(words) - len(set(words))) / len(words)
        if repeated_ratio > 0.3:
            result = "🚨 Fake Review (Too repetitive or unnatural language)"
            return render_template('index.html', prediction=result)

    # --- Preprocess text exactly as training ---
    cleaned_text = clean_text(review_text)

    # TF-IDF transform
    X_text = vectorizer.transform([cleaned_text]).toarray()

    # --- Compute numeric features ---
    try:
        rating = float(rating_raw)
    except:
        rating = 0.0

    text_length = len(review_text)
    word_count = len(review_text.split())
    time_diff_min = compute_time_diff_min(post_timestamp, review_timestamp)
    username_freq = username_counts.get(username, 0)
    ip_freq = ip_counts.get(ip_address, 0)

    X_num = np.array([[rating, text_length, word_count, time_diff_min, username_freq, ip_freq]], dtype=float)

    # --- Combine TF-IDF + numeric features ---
    X_input = np.hstack((X_text, X_num))

    # --- Predict ---
    try:
        prediction = model.predict(X_input)[0]
        result = "✅ Genuine Review" if prediction == 1 else "🚨 Fake Review"
    except Exception as e:
        result = f"Prediction error: {e}"

    return render_template('index.html',
                           prediction=result,
                           ip_address=ip_address,
                           review_text=review_text,
                           category=category,
                           rating=rating_raw,
                           username=username,
                           post_timestamp=post_timestamp,
                           review_timestamp=review_timestamp)

if __name__ == '__main__':
    app.run(debug=True)
