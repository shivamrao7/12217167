from flask import Flask, request, jsonify, redirect
import sqlite3
import string
import random
import time
from datetime import datetime, timedelta
import os
import sys
sys.path.append('./Logging Middleware')
from logger import log_request

app = Flask(__name__)

@app.after_request
def after_request(response):
    log_request(
        request.method,
        request.path,
        response.status_code,
        request.remote_addr
    )
    return response

def get_db():
    conn = sqlite3.connect('urls.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS urls
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         long_url TEXT NOT NULL,
         shortcode TEXT UNIQUE NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         expires_at TIMESTAMP NOT NULL)
    ''')
    conn.commit()
    conn.close()

def generate_shortcode():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

def is_valid_shortcode(shortcode):
    return all(c in string.ascii_letters + string.digits for c in shortcode)

@app.route('/shorten', methods=['POST'])
def shorten_url():
    data = request.get_json()
    
    if not data or 'long_url' not in data:
        return jsonify({'error': 'long_url is required'}), 400
    
    long_url = data['long_url']
    validity_minutes = data.get('validity_in_minutes', 30)
    custom_shortcode = data.get('custom_shortcode')
    
    if custom_shortcode and not is_valid_shortcode(custom_shortcode):
        return jsonify({'error': 'custom_shortcode must be alphanumeric'}), 400
    
    conn = get_db()
    
    if custom_shortcode:
        existing = conn.execute('SELECT id FROM urls WHERE shortcode = ?', (custom_shortcode,)).fetchone()
        if existing:
            conn.close()
            return jsonify({'error': 'custom_shortcode already exists'}), 409
        shortcode = custom_shortcode
    else:
        while True:
            shortcode = generate_shortcode()
            existing = conn.execute('SELECT id FROM urls WHERE shortcode = ?', (shortcode,)).fetchone()
            if not existing:
                break
    
    expires_at = datetime.now() + timedelta(minutes=validity_minutes)
    
    conn.execute('INSERT INTO urls (long_url, shortcode, expires_at) VALUES (?, ?, ?)',
                (long_url, shortcode, expires_at))
    conn.commit()
    conn.close()
    
    short_url = request.host_url.rstrip('/') + '/' + shortcode
    return jsonify({'short_url': short_url, 'shortcode': shortcode}), 201

@app.route('/<shortcode>')
def redirect_to_url(shortcode):
    conn = get_db()
    url_data = conn.execute('SELECT long_url, expires_at FROM urls WHERE shortcode = ?', (shortcode,)).fetchone()
    conn.close()
    
    if not url_data:
        return jsonify({'error': 'shortcode not found'}), 404
    
    expires_at = datetime.fromisoformat(url_data['expires_at'])
    if datetime.now() > expires_at:
        return jsonify({'error': 'url has expired'}), 410
    
    return redirect(url_data['long_url'], code=302)

@app.route('/stats/<shortcode>')
def get_stats(shortcode):
    conn = get_db()
    url_data = conn.execute('SELECT long_url, shortcode, created_at, expires_at FROM urls WHERE shortcode = ?', (shortcode,)).fetchone()
    conn.close()
    
    if not url_data:
        return jsonify({'error': 'shortcode not found'}), 404
    
    created_at = datetime.fromisoformat(url_data['created_at'])
    expires_at = datetime.fromisoformat(url_data['expires_at'])
    now = datetime.now()
    
    is_expired = now > expires_at
    time_until_expiry = (expires_at - now).total_seconds() if not is_expired else 0
    
    stats = {
        'shortcode': url_data['shortcode'],
        'long_url': url_data['long_url'],
        'created_at': url_data['created_at'],
        'expires_at': url_data['expires_at'],
        'is_expired': is_expired,
        'time_until_expiry_seconds': int(time_until_expiry),
        'total_lifetime_minutes': int((expires_at - created_at).total_seconds() / 60)
    }
    
    return jsonify(stats), 200

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)