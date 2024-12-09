from flask import Flask, render_template, request, jsonify
import hashlib
import json
import time
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# Path to the JSON file where the blockchain will be stored
BLOCKCHAIN_FILE = 'blockchain.json'

class Blockchain:
    def __init__(self):
        self.chain = []
        self.load_chain()

    def create_genesis_block(self):
        genesis_block = self.create_block(previous_hash='0', unique_id='GENESIS')
        self.chain.append(genesis_block)
        self.save_chain()

    def create_block(self, previous_hash, unique_id):
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        readable_timestamp = datetime.now(malaysia_tz).strftime('%Y-%m-%d %I:%M:%S %p')

        block = {
            'index': len(self.chain) + 1,
            'timestamp': readable_timestamp,
            'previous_hash': previous_hash,
            'unique_id': unique_id,
            'hash': ''
        }
        block['hash'] = self.hash_block(block)
        return block

    def hash_block(self, block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def add_block(self, block):
        self.chain.append(block)
        self.save_chain()

    def get_latest_block(self):
        return self.chain[-1]

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block['previous_hash'] != previous_block['hash']:
                return False

            current_block_hash = self.hash_block(current_block)
            if current_block['hash'] != current_block_hash:
                return False
        return True

    def save_chain(self):
        with open(BLOCKCHAIN_FILE, 'w') as f:
            json.dump(self.chain, f, indent=4)

    def load_chain(self):
        if os.path.exists(BLOCKCHAIN_FILE):
            with open(BLOCKCHAIN_FILE, 'r') as f:
                self.chain = json.load(f)
        else:
            self.create_genesis_block()


blockchain = Blockchain()

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_files' not in request.files:
        return jsonify({"error": "No files uploaded."}), 400

    pdf_files = request.files.getlist('pdf_files')  # Retrieve multiple files
    upload_results = []

    for pdf_file in pdf_files:
        pdf_data = pdf_file.read()
        pdf_hash = hashlib.sha256(pdf_data).hexdigest()
        latest_block = blockchain.get_latest_block()
        new_block = blockchain.create_block(latest_block['hash'], pdf_hash)
        blockchain.add_block(new_block)

        upload_results.append({
            "file_name": pdf_file.filename,
            "pdf_hash": pdf_hash,
            "block_index": new_block['index']
        })

    return jsonify(upload_results)

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    return jsonify(blockchain.chain)

if __name__ == '__main__':
    app.run(debug=True)
