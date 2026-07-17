import secrets
import string
import hashlib
import base64
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image
from cryptography.fernet import Fernet

# =========================================================================================
# 🔐 KEY GENERATION
# =========================================================================================

def generate_secure_key(length=32):
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?/"
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_fernet_key_from_passphrase(passphrase):
    hashed = hashlib.sha256(passphrase.encode()).digest()
    return base64.urlsafe_b64encode(hashed)

# =========================================================================================
# 🖼️ IMAGE STEGANOGRAPHY (UPDATED)
# =========================================================================================

def encode_image_steganography(image_file, secret_text, passphrase):
    image = Image.open(image_file).convert("RGB")
    encoded = image.copy()

    key = generate_fernet_key_from_passphrase(passphrase)
    fernet = Fernet(key)
    encrypted_message = fernet.encrypt(secret_text.encode('utf-8')).decode('utf-8')

    binary_secret = ''.join(format(ord(c), '08b') for c in encrypted_message)
    binary_secret += '1111111111111110'  # Terminator

    index = 0
    for y in range(encoded.height):
        for x in range(encoded.width):
            if index >= len(binary_secret):
                break
            r, g, b = encoded.getpixel((x, y))
            if index < len(binary_secret):
                r = (r & ~1) | int(binary_secret[index])
                index += 1
            if index < len(binary_secret):
                g = (g & ~1) | int(binary_secret[index])
                index += 1
            if index < len(binary_secret):
                b = (b & ~1) | int(binary_secret[index])
                index += 1
            encoded.putpixel((x, y), (r, g, b))
        if index >= len(binary_secret):
            break

    buffer = BytesIO()
    encoded.save(buffer, format="PNG")
    buffer.seek(0)
    return ContentFile(buffer.read(), name="encoded_image.png")


def decode_image_steganography(image_file, passphrase):
    image = Image.open(image_file).convert("RGB")
    binary_data = ""

    for y in range(image.height):
        for x in range(image.width):
            r, g, b = image.getpixel((x, y))
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)

    terminator = '1111111111111110'
    end_index = binary_data.find(terminator)
    if end_index == -1:
        return "❌ No hidden message found or image corrupted."

    message_bits = binary_data[:end_index]
    chars = [message_bits[i:i+8] for i in range(0, len(message_bits), 8)]

    try:
        encrypted_text = ''.join([chr(int(b, 2)) for b in chars])
    except Exception:
        return "❌ Decoding failed due to invalid characters."

    try:
        key = generate_fernet_key_from_passphrase(passphrase)
        fernet = Fernet(key)
        decrypted_message = fernet.decrypt(encrypted_text.encode()).decode('utf-8')
        return decrypted_message
    except Exception:
        return "❌ Incorrect passphrase or corrupted message."
