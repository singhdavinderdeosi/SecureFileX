import os
import json
import base64
import secrets
import uuid
import qrcode

from django.conf import settings
from django.utils.text import get_valid_filename

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from hashlib import sha256
from base64 import urlsafe_b64encode

# ------------------------ Utility Functions ------------------------

def generate_secure_key(length=32):
    return secrets.token_bytes(length)

def generate_key_from_passphrase(passphrase, algorithm):
    algo = algorithm.upper()
    hashed = sha256(passphrase.encode()).digest()
    if algo == "FERNET":
        return urlsafe_b64encode(hashed)
    elif algo in ("CHACHA20", "AES-GCM"):
        return hashed
    else:
        raise ValueError("Unsupported algorithm for key generation")

def generate_pin():
    return secrets.token_hex(3)

def generate_qr_code(data, output_path):
    qr = qrcode.make(data)
    qr.save(output_path)

def rel_path(p):
    return os.path.relpath(p, settings.MEDIA_ROOT).replace("\\", "/")

# ------------------------ AI-Based Algorithm Suggestion ------------------------

def recommend_encryption_algorithm(file_name, file_size, sensitivity_level="medium"):
    ext = os.path.splitext(file_name)[1].lower()
    if ext in ['.jpg', '.png', '.jpeg', '.gif'] or file_size > 5 * 1024 * 1024:
        return "CHACHA20"
    elif ext in ['.pdf', '.docx', '.xlsx'] and file_size < 2 * 1024 * 1024:
        return "AES-GCM"
    elif sensitivity_level == "high":
        return "RSA" if file_size < 190 else "AES-GCM"
    else:
        return "FERNET"

# ------------------------ Encryption ------------------------

def encrypt_file(file, algorithm, user, user_key=None):
    try:
        content = file.read()
        original_name = file.name
        algo = algorithm.upper()
        recommended_algo = recommend_encryption_algorithm(original_name, len(content))

        key, nonce, tag = None, None, None
        rsa_private_key = None

        # Key generation
        if user_key:
            key = generate_key_from_passphrase(user_key, algo)
        else:
            if algo == "FERNET":
                key = Fernet.generate_key()
            elif algo in ("CHACHA20", "AES-GCM"):
                key = generate_secure_key(32)
            elif algo == "RSA":
                rsa_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
                key = rsa_private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                )
            else:
                return {"success": False, "error": f"❌ Unsupported algorithm: {algo}"}

        # Save structure
        enc_dir = os.path.join(settings.MEDIA_ROOT, "encrypted", user.username)
        os.makedirs(enc_dir, exist_ok=True)

        safe_name = get_valid_filename(os.path.splitext(original_name)[0])
        uid = uuid.uuid4().hex
        base_filename = f"{safe_name}_{uid}"

        encrypted_path = os.path.join(enc_dir, f"{base_filename}.enc")
        metadata_path = os.path.join(enc_dir, f"{base_filename}.json")
        keyfile_path = os.path.join(enc_dir, f"{base_filename}.keys")
        qr_path = os.path.join(enc_dir, f"{base_filename}_qr.png")

        # Actual Encryption
        if algo == "FERNET":
            encrypted = Fernet(key).encrypt(content)

        elif algo == "CHACHA20":
            nonce = generate_secure_key(16)
            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
            encrypted = cipher.encryptor().update(content)

        elif algo == "AES-GCM":
            nonce = generate_secure_key(12)
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(content) + encryptor.finalize()
            tag = encryptor.tag

        elif algo == "RSA":
            if len(content) > 190:
                return {"success": False, "error": "❌ RSA can only encrypt small files (≤190 bytes).\nUse AES-GCM or Fernet for larger files."}
            try:
                public_key = rsa_private_key.public_key()
                encrypted = public_key.encrypt(
                    content,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            except Exception as e:
                return {"success": False, "error": f"❌ RSA encryption error: {str(e)}"}

        # Save Encrypted File
        with open(encrypted_path, "wb") as f:
            f.write(encrypted)

        # Save Metadata and Keyfile
        metadata = {
            "original_filename": original_name,
            "algorithm": algo,
            "key": base64.b64encode(key).decode() if key else None,
            "nonce": base64.b64encode(nonce).decode() if nonce else None,
            "tag": base64.b64encode(tag).decode() if tag else None,
        }
        with open(metadata_path, "w") as mf:
            json.dump(metadata, mf)
        with open(keyfile_path, "w") as kf:
            json.dump({k: metadata[k] for k in ("key", "nonce", "tag")}, kf)

        # QR Code
        pin = generate_pin()
        site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        metadata_url = f"{site_url}/share/{pin}/"
        generate_qr_code(metadata_url, qr_path)

        return {
            "success": True,
            "encrypted_filename": os.path.basename(encrypted_path),
            "encrypted_data": rel_path(encrypted_path),
            "download_url": settings.MEDIA_URL + rel_path(encrypted_path),
            "metadata_path": rel_path(metadata_path),
            "metadata_url": settings.MEDIA_URL + rel_path(metadata_path),
            "keyfile_url": settings.MEDIA_URL + rel_path(keyfile_path),
            "qr_code_url": settings.MEDIA_URL + rel_path(qr_path),
            "original_filename": original_name,
            "algorithm": algo,
            "pin": pin,
            "key": metadata["key"],
            "salt": None,
            "recommended": recommended_algo
        }

    except Exception as e:
        return {"success": False, "error": f"❌ Encryption failed: {str(e)}"}

# ------------------------ Decryption ------------------------

def decrypt_file(file, user, user_key=None):
    try:
        enc_name = file.name
        content = file.read()
        base = os.path.splitext(enc_name)[0]

        enc_dir = os.path.join(settings.MEDIA_ROOT, "encrypted", user.username)
        metadata_path = os.path.join(enc_dir, f"{base}.json")

        if not os.path.exists(metadata_path):
            return {"success": False, "error": "❌ Metadata file not found."}

        with open(metadata_path, "r") as mf:
            metadata = json.load(mf)

        algo = metadata.get("algorithm", "").upper()
        key = base64.b64decode(metadata.get("key", "")) if metadata.get("key") else None
        nonce = base64.b64decode(metadata.get("nonce", "")) if metadata.get("nonce") else None
        tag = base64.b64decode(metadata.get("tag", "")) if metadata.get("tag") else None
        orig_name = metadata.get("original_filename", "decrypted_output")

        if user_key:
            try:
                key = generate_key_from_passphrase(user_key, algo)
            except Exception as e:
                return {"success": False, "error": f"❌ Invalid passphrase: {str(e)}"}

        if not key:
            return {"success": False, "error": "❌ Missing or invalid decryption key."}

        # Decrypt
        if algo == "FERNET":
            decrypted = Fernet(key).decrypt(content)

        elif algo == "CHACHA20":
            if not nonce:
                return {"success": False, "error": "❌ Missing nonce for ChaCha20."}
            decrypted = Cipher(algorithms.ChaCha20(key, nonce), mode=None).decryptor().update(content)

        elif algo == "AES-GCM":
            if not (nonce and tag):
                return {"success": False, "error": "❌ Missing nonce or tag for AES-GCM."}
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
            decrypted = cipher.decryptor().update(content) + cipher.decryptor().finalize()

        elif algo == "RSA":
            try:
                private_key = serialization.load_pem_private_key(key, password=None)
                decrypted = private_key.decrypt(
                    content,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            except Exception as e:
                return {"success": False, "error": f"❌ RSA decryption failed: {str(e)}"}

        else:
            return {"success": False, "error": f"❌ Unsupported algorithm: {algo}"}

        return {
            "success": True,
            "decrypted_content": decrypted,
            "original_filename": orig_name,
            "algorithm": algo
        }

    except Exception as e:
        return {"success": False, "error": f"⚠️ Decryption error: {str(e)}"}
