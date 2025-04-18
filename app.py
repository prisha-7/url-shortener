# app.py
from flask import Flask, request, redirect, jsonify, abort
import hashlib
import base64
import os # Import os to read environment variables
import redis # Import redis

app = Flask(__name__)

# --- Use Redis instead of the Python dictionary ---
# Get Redis host from environment variable, default to 'localhost' if not set
# This 'localhost' default is useful for local testing without K8s
# In Kubernetes, we will set REDIS_HOST to the Redis service name ('redis-service')
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379)) # Default Redis port

# Connect to Redis - decode_responses=True makes it return strings instead of bytes
try:
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    redis_client.ping() # Check connection
    print(f"Successfully connected to Redis at {redis_host}:{redis_port}")
except redis.exceptions.ConnectionError as e:
    print(f"Error connecting to Redis at {redis_host}:{redis_port}: {e}")
    # You might want to exit or handle this more gracefully in a real app
    redis_client = None # Set client to None if connection fails

# url_map = {} # Remove the dictionary

def generate_short_code(long_url):
    """Generates a short code (simple hash-based approach)."""
    hasher = hashlib.sha256(long_url.encode('utf-8'))
    short_code = base64.urlsafe_b64encode(hasher.digest()[:6]).decode('utf-8').rstrip('=')
    return short_code

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Accepts a long URL and returns a short URL."""
    if not redis_client:
         return jsonify({"error": "Redis connection failed"}), 500

    if not request.json or 'url' not in request.json:
        abort(400, description="Missing 'url' in JSON payload")

    long_url = request.json['url']

    if not long_url.startswith(('http://', 'https://')):
         return jsonify({"error": "Invalid URL format. Must start with http:// or https://"}), 400

    short_code = generate_short_code(long_url)

    # --- Store the mapping in Redis ---
    # Use SET command. You could add expiration using SETEX if needed.
    redis_client.set(short_code, long_url)

    base_url = request.host_url # e.g., http://<service-ip>:<port>/
    short_url = f"{base_url}{short_code}"

    return jsonify({"short_url": short_url, "long_url": long_url})

@app.route('/<short_code>', methods=['GET'])
def redirect_to_long_url(short_code):
    """Redirects a short code to its original long URL using Redis."""
    if not redis_client:
         return jsonify({"error": "Redis connection failed"}), 500

    # --- Retrieve the long URL from Redis ---
    long_url = redis_client.get(short_code)

    if long_url:
        return redirect(long_url, code=302)
    else:
        abort(404, description="Short URL not found")

# Add a health check endpoint (good practice)
@app.route('/healthz', methods=['GET'])
def health_check():
    try:
        if redis_client and redis_client.ping():
            return jsonify({"status": "ok", "redis_connection": "ok"}), 200
        else:
             return jsonify({"status": "error", "redis_connection": "failed"}), 500
    except Exception as e:
         return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Use port 5000 inside the container
    app.run(host='0.0.0.0', port=5000, debug=False) # Set debug=False for production/K8s
