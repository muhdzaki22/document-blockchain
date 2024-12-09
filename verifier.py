from flask import Flask, request, jsonify, render_template
import hashlib
import json
import os

app = Flask(__name__)

BLOCKCHAIN_FILE = 'blockchain.json'

def load_blockchain():
    if os.path.exists(BLOCKCHAIN_FILE):
        with open(BLOCKCHAIN_FILE, 'r') as f:
            return json.load(f)
    return []

@app.route('/')
def index():
    return render_template('verifier.html')

@app.route('/verify', methods=['POST'])
def verify_pdfs():
    if 'pdf_files' not in request.files:
        return jsonify({"status": "error", "message": "No files uploaded."})

    files = request.files.getlist('pdf_files')
    results = []
    blockchain = load_blockchain()

    for pdf_file in files:
        pdf_data = pdf_file.read()
        pdf_hash = hashlib.sha256(pdf_data).hexdigest()

        status = "not_verified"
        for block in blockchain:
            if block.get('unique_id') == pdf_hash:
                status = "verified"
                break

        results.append({"filename": pdf_file.filename, "status": status, "pdf_hash": pdf_hash})

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5001)

