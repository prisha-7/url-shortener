import hashlib
import random
import string
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# In-memory storage for URL mappings
url_store = {}

def generate_short_code(url):
    """Generate a unique short URL code using a hash."""
    return hashlib.md5(url.encode()).hexdigest()[:6]  # 6-char hash

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    long_url = data.get('url')

    if not long_url:
        return jsonify({"error": "Missing URL"}), 400

    short_code = generate_short_code(long_url)
    url_store[short_code] = long_url  # Store in-memory

    short_url = f"http://localhost:5000/short/{short_code}"
    return jsonify({"short_url": short_url})

@app.route('/short/<short_code>', methods=['GET'])
def redirect_url(short_code):
    long_url = url_store.get(short_code)

    if not long_url:
        return jsonify({"error": "Short URL not found"}), 404

    return redirect(long_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
