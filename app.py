import os
import io
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

def generate_key():
    return os.urandom(32)

def encrypt_data(data, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + encrypted_data)

def decrypt_data(encrypted_data, key):
    decoded_data = base64.b64decode(encrypted_data)
    iv = decoded_data[:16]
    ciphertext = decoded_data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    action = request.form['action']
    
    try:
        if action == 'encrypt':
            key = generate_key()
            encrypted_data = encrypt_data(file.read(), key)
            encryption_key = base64.b64encode(key).decode()
            return jsonify({
                'action': 'encrypt',
                'key': encryption_key,
                'filename': f"{secure_filename(file.filename)}.encrypted",
                'data': base64.b64encode(encrypted_data).decode()
            })
        elif action == 'decrypt':
            key = base64.b64decode(request.form['key'])
            decrypted_data = decrypt_data(file.read(), key)
            return jsonify({
                'action': 'decrypt',
                'filename': f"{secure_filename(file.filename)[:-10] if file.filename.endswith('.encrypted') else secure_filename(file.filename)}.decrypted",
                'data': base64.b64encode(decrypted_data).decode()
            })
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)