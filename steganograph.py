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

# Blockchain class implementation
class Blockchain:
    def __init__(self):
        self.chain = []
        self.load_chain()

    def create_genesis_block(self):
        # The first block is a special "genesis" block
        genesis_block = self.create_block(previous_hash='0')
        self.chain.append(genesis_block)
        self.save_chain()

    def create_block(self, previous_hash):
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        readable_timestamp = datetime.now(malaysia_tz).strftime('%Y-%m-%d %I:%M:%S %p')

        # Your dictionary
        block = {
            'index': len(self.chain) + 1,
            'timestamp': readable_timestamp,
            'previous_hash': previous_hash,
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
        # Check the validity of the blockchain by comparing hashes
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check the hash of the current block and the previous block's hash
            if current_block['previous_hash'] != previous_block['hash']:
                return False

            # Verify the current block's hash
            current_block_hash = self.hash_block(current_block)
            if current_block['hash'] != current_block_hash:
                return False
        return True

    def save_chain(self):
        # Save the blockchain to a JSON file
        with open(BLOCKCHAIN_FILE, 'w') as f:
            json.dump(self.chain, f, indent=4)

    def load_chain(self):
        # Load the blockchain from the JSON file if it exists
        if os.path.exists(BLOCKCHAIN_FILE):
            with open(BLOCKCHAIN_FILE, 'r') as f:
                self.chain = json.load(f)
        else:
            # If the file does not exist, create the genesis block
            self.create_genesis_block()


blockchain = Blockchain()

# Function to convert a string into binary representation
def text_to_binary(text):
    return ''.join(f"{ord(char):08b}" for char in text)

# Function to convert binary data into zero-width characters
def binary_to_zero_width(binary):
    return binary.replace('0', '\u200B').replace('1', '\u200C')

# Function to hide a secret message within the middle of the public text
def encode_message(public_text, private_text):
    binary_message = text_to_binary(private_text)
    encoded_message = binary_to_zero_width(binary_message)
    mid_index = len(public_text) // 2
    return public_text[:mid_index] + '\u200D' + encoded_message + '\u200D' + public_text[mid_index:]

# Function to decode the hidden message from a steganographed text
def decode_message(stego_text):
    parts = stego_text.split('\u200D')
    if len(parts) < 3:
        return "No hidden message found."
    encoded_message = parts[1]
    binary_message = encoded_message.replace('\u200B', '0').replace('\u200C', '1')
    chars = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    return ''.join([chr(int(char, 2)) for char in chars])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    public_text = request.form['public_text']
    private_text = request.form['private_text']
    
    # Generate the stego text
    stego_text = encode_message(public_text, private_text)

    # Create the new block, ensuring the hash of the latest block is used
    latest_block = blockchain.get_latest_block()
    new_block = blockchain.create_block(latest_block['hash'])
    blockchain.add_block(new_block)

    # Generate SHA-256 hash of the stego_text as a unique identifier
    unique_id = hashlib.sha256(new_block['hash'].encode()).hexdigest()

    return jsonify({"stego_text": stego_text, "unique_id": unique_id})

@app.route('/decode', methods=['POST'])
def decode():
    stego_text = request.form['stego_text']
    decoded_message = decode_message(stego_text)
    return jsonify({"decoded_message": decoded_message})

@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    # Return the blockchain data as a JSON response
    chain_data = []
    for block in blockchain.chain:
        # Reorder keys so that 'hash' is the last element in the block
        block_data = {
            'index': block['index'],
            'timestamp': block['timestamp'],
            'previous_hash': block['previous_hash'],
            'hash': block['hash']  # 'hash' is placed last
        }
        chain_data.append(block_data)
    return jsonify(chain_data)


if __name__ == '__main__':
    app.run(debug=True)
