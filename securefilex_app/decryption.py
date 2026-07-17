import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from securefilex_app.models import FileMetadata, ActivityLog


# -------------------------------
# Logging
# -------------------------------

def log_activity(user, action, filename, algorithm, details=""):
    ActivityLog.objects.create(
        user=user,
        action=action,
        details=details or f"{action} performed on {filename}",
        timestamp=timezone.now()
    )


# -------------------------------
# OTP Verification + Metadata Fetch
# -------------------------------

def verify_otp_and_get_metadata(user, filename, otp):
    try:
        metadata = FileMetadata.objects.get(user=user, filename=filename)
    except FileMetadata.DoesNotExist:
        raise ValueError("No encryption metadata found.")

    # OPTIONAL: This assumes OTP is logged in ActivityLog details (basic approach)
    recent_logs = ActivityLog.objects.filter(user=user, action="Encrypt", filename=filename).order_by('-timestamp')[:5]
    for log in recent_logs:
        if f"OTP: {otp}" in log.details:
            return metadata  # Valid OTP match

    raise PermissionError("Invalid OTP.")


# -------------------------------
# Core Decryption Logic
# -------------------------------

def decrypt_file(user, filename, otp):
    metadata = verify_otp_and_get_metadata(user, filename, otp)
    algorithm = metadata.algorithm.upper()
    key = metadata.key
    nonce = metadata.nonce
    tag = metadata.tag

    # Load encrypted file
    encrypted_path = os.path.join(settings.MEDIA_ROOT, "encrypted", user.username, filename + ".enc")
    if not os.path.exists(encrypted_path):
        raise FileNotFoundError("Encrypted file not found.")

    with open(encrypted_path, 'rb') as f:
        encrypted_data = f.read()

    decrypted_data = None

    if algorithm == "FERNET":
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

    elif algorithm == "CHACHA20":
        if not nonce:
            raise ValueError("Nonce is required for ChaCha20.")
        cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data)

    elif algorithm == "AES-GCM":
        if not nonce or not tag:
            raise ValueError("Nonce and Tag are required for AES-GCM.")
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    elif algorithm == "RSA":
        private_key = serialization.load_pem_private_key(key, password=None)
        decrypted_data = private_key.decrypt(
            encrypted_data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )

    else:
        raise ValueError("Unsupported decryption algorithm.")

    # Save decrypted file
    decrypted_filename = filename.replace(".enc", "") if filename.endswith(".enc") else "decrypted_" + filename
    decrypted_path = os.path.join(settings.MEDIA_ROOT, "decrypted", user.username)
    os.makedirs(decrypted_path, exist_ok=True)

    full_path = os.path.join(decrypted_path, decrypted_filename)
    with open(full_path, 'wb') as f:
        f.write(decrypted_data)

    # Log activity
    log_activity(user, "Decrypt", filename, algorithm, "Decryption successful")

    return ContentFile(decrypted_data, name=decrypted_filename)
