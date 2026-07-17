from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import (
    HttpResponse, JsonResponse, Http404, HttpResponseBadRequest,
    HttpResponseForbidden, FileResponse
)
from django.conf import settings
from django.utils.text import get_valid_filename
from django.utils.timezone import now
from django.core.files.storage import default_storage, FileSystemStorage
from django.contrib import messages

# 🔐 Authentication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

# 📦 Standard Library
import os
import uuid
import json
import base64
import logging
from io import BytesIO
from datetime import datetime
from urllib.parse import quote

# 🖼️ Media Handling
import mimetypes
from PIL import Image
import qrcode
import socket

# 🔐 Encryption Libraries
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

# 📁 Local App Imports
from .models import EncryptionAlgorithm
from .encryption.encryption import encrypt_file, decrypt_file
from .steganography import hide_message_in_image, extract_message_from_image

# 📂 File storage root
BASE_DIR = settings.MEDIA_ROOT
# AUTHENTICATION

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Explicitly set backend to avoid ValueError
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)

            return redirect('profile')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("profile")
        messages.error(request, "Invalid username or password.")
    return render(request, "registration/login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("welcome")


# USER DASHBOARD 

@login_required
def profile(request):
    return render(request, 'account.html')
def get_local_ip():
    """Get the local IP address of the machine running the server."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return '127.0.0.1'

@login_required
def share(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        filename = get_valid_filename(uploaded_file.name)
        filename = fs.save(filename, uploaded_file)
        file_url = fs.url(filename)

        # Generate a 6-digit hex PIN 
        pin = os.urandom(3).hex()

        # Create necessary directories
        pins_dir = os.path.join(settings.MEDIA_ROOT, 'pins')
        qr_codes_dir = os.path.join(settings.MEDIA_ROOT, 'qr_codes')
        os.makedirs(pins_dir, exist_ok=True)
        os.makedirs(qr_codes_dir, exist_ok=True)

        # Save the PIN securely
        try:
            with open(os.path.join(pins_dir, f'{filename}.pin'), 'w', encoding='utf-8') as f:
                f.write(pin)
        except Exception as e:
            return render(request, 'share.html', {'error': f"Failed to save PIN: {str(e)}"})

        # Build shareable URL using local IP
        local_ip = get_local_ip()
        share_url = f"http://{local_ip}:8000{reverse('verify_pin', args=[quote(filename), pin])}"

        # Generate QR Code
        qr_filename = f'{filename}_qr.png'
        qr_path = os.path.join(qr_codes_dir, qr_filename)
        try:
            qrcode.make(share_url).save(qr_path)
        except Exception as e:
            return render(request, 'share.html', {'error': f"QR Code generation failed: {str(e)}"})

        qr_code_url = os.path.join(settings.MEDIA_URL, 'qr_codes', qr_filename).replace('\\', '/')

        return render(request, 'share.html', {
            'filename': filename,
            'file_url': file_url,
            'pin': pin,
            'qr_code_url': qr_code_url,
            'share_url': share_url,
            'success': True
        })

    return render(request, 'share.html')



def verify_pin(request, filename, pin):
    if any(sub in filename for sub in ['/', '\\', '..']):
        return HttpResponseForbidden("❌ Invalid filename.")

    pin_dir = os.path.join(settings.MEDIA_ROOT, 'pins')
    pin_path = os.path.join(pin_dir, f'{filename}.pin')

    if not os.path.exists(pin_path):
        return HttpResponseForbidden("❌ File or PIN not found.")

    try:
        with open(pin_path, 'r', encoding='utf-8') as f:
            stored_pin = f.read().strip()
    except Exception as e:
        return HttpResponseForbidden(f"❌ Error reading PIN file: {str(e)}")

    if stored_pin == pin:
        media_url = f"{settings.MEDIA_URL}{quote(filename)}"
        return redirect(media_url)
    else:
        return HttpResponseForbidden("❌ Incorrect PIN.")

@login_required
def result(request):
    return render(request, 'result.html', {
        'file_url': request.GET.get('file_url'),
        'message': request.GET.get('message'),
        'extracted_text': request.GET.get('extracted_text'),
        'generated_key': request.GET.get('generated_key'),
        'salt': request.GET.get('salt'),
        'algorithm': request.GET.get('algorithm'),
        'action': request.GET.get('action'),  # 'encryption' or 'decryption'
        'timestamp': request.GET.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    })


@login_required
def encryption_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        algorithm = request.POST.get('algorithm')
        user_key = request.POST.get('password')

        if not uploaded_file or not algorithm:
            msg = "❗ Both file and algorithm are required."
            context = {"message": msg}
            return JsonResponse({"success": False, "error": msg}, status=400) if is_ajax else render(request, 'result.html', context)

        try:
            result = encrypt_file(
                file=uploaded_file,
                algorithm=algorithm,
                user=request.user,
                user_key=user_key
            )

            filename = result.get('encrypted_filename')
            download_url = result.get('download_url')
            metadata_url = result.get('metadata_url')
            key_file_url = result.get('keyfile_url')
            qr_code_url = result.get('qr_code_url')  # Optional if QR shown
            generated_key = result.get('key')
            salt = result.get('salt')
            recommended = result.get('recommended')

            if not filename or not download_url:
                raise ValueError("Missing 'encrypted_filename' or 'download_url' in result.")

            shortlink = request.build_absolute_uri(reverse('download_file', args=[filename]))

            context = {
                "file_url": download_url,
                "message": f"✅ Encrypted file saved: {filename}",
                "generated_key": generated_key,
                "salt": salt,
                "algorithm": algorithm,
                "action": "encryption",
                "recommended": recommended,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "encrypted_filename": filename,
                    "download_url": download_url,
                    "metadata_url": metadata_url,
                    "key_file_url": key_file_url,
                    "qr_code_url": qr_code_url,
                    "shortlink": shortlink,
                    "recommended": recommended,
                    **context
                })

            return render(request, 'result.html', context)

        except Exception as e:
            msg = f"❌ Encryption failed: {str(e)}"
            return JsonResponse({"success": False, "error": msg}, status=500) if is_ajax else render(request, 'result.html', {"message": msg})

    return render(request, 'encrypt.html')


@login_required
def decryption_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        uploaded_file = request.FILES.get('enc_file')  # Must match input name
        user_key = request.POST.get('password')

        if not uploaded_file:
            msg = "❗ Encrypted file is required."
            return JsonResponse({"success": False, "error": msg}, status=400) if is_ajax else render(request, 'result.html', {"message": msg})

        try:
            result = decrypt_file(
                file=uploaded_file,
                user=request.user,
                user_key=user_key
            )

            if result.get("success"):
                decrypted_content = result.get("decrypted_content")
                filename = result.get("original_filename") or "decrypted_file"
                algorithm = result.get("algorithm")
                extracted_text = result.get("extracted_text")

                user_dir = os.path.join("decrypted_temp", request.user.username)
                full_dir_path = os.path.join(settings.MEDIA_ROOT, user_dir)
                os.makedirs(full_dir_path, exist_ok=True)

                full_file_path = os.path.join(full_dir_path, filename)
                with open(full_file_path, 'wb') as f:
                    f.write(decrypted_content)

                download_url = os.path.join(settings.MEDIA_URL, user_dir, filename).replace('\\', '/')

                context = {
                    "file_url": download_url,
                    "message": "✅ File decrypted successfully.",
                    "extracted_text": extracted_text,
                    "algorithm": algorithm,
                    "action": "decryption",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }

                return JsonResponse({"success": True, "download_url": download_url, **context}) if is_ajax else render(request, 'result.html', context)

            else:
                msg = result.get("error", "❌ Unknown error during decryption.")
                return JsonResponse({"success": False, "error": msg}, status=400) if is_ajax else render(request, "result.html", {"message": msg})

        except Exception as e:
            msg = f"❌ Decryption failed: {str(e)}"
            return JsonResponse({"success": False, "error": msg}, status=500) if is_ajax else render(request, "result.html", {"message": msg})

    return render(request, 'decrypt.html')

@login_required
def download_file(request, filename):
    if '/' in filename or '\\' in filename or '..' in filename:
        raise Http404("Invalid file name.")

    # Check both 'decrypted_temp' and 'encrypted' folders if needed
    search_dirs = [
        os.path.join(settings.MEDIA_ROOT, 'decrypted_temp', request.user.username),
        os.path.join(settings.MEDIA_ROOT, 'encrypted', request.user.username)
    ]

    file_path = None
    for directory in search_dirs:
        test_path = os.path.join(directory, filename)
        if os.path.isfile(test_path):
            file_path = test_path
            break

    if not file_path:
        raise Http404("The requested file was not found.")

    mime_type, _ = mimetypes.guess_type(file_path)
    try:
        return FileResponse(
            open(file_path, 'rb'),
            content_type=mime_type or 'application/octet-stream',
            as_attachment=True,
            filename=filename
        )
    except Exception as e:
        raise Http404(f"Download error: {str(e)}")

# STEGANOGRAPHY
@login_required
def steganography_view(request):
    if request.method == 'POST':
        mode = request.POST.get('mode', '').strip()

        if mode == 'hide':
            image_file = request.FILES.get('image')
            secret_message = request.POST.get('message', '').strip()

            if not image_file:
                return JsonResponse({'message': '❌ Please upload an image file.', 'success': False}, status=400)
            if not secret_message:
                return JsonResponse({'message': '❌ Secret message cannot be empty.', 'success': False}, status=400)

            result = hide_message_in_image(image_file, secret_message)
            return JsonResponse(result, status=200 if result['success'] else 400)

        elif mode == 'extract':
            stego_image_file = request.FILES.get('stego_image')

            if not stego_image_file:
                return JsonResponse({'message': '❌ Please upload a stego image.', 'success': False}, status=400)

            result = extract_message_from_image(stego_image_file)
            return JsonResponse(result, status=200 if result['success'] else 400)

        # Invalid mode
        return JsonResponse({'message': '❌ Invalid operation mode.', 'success': False}, status=400)

    # For GET requests, render the UI template
    return render(request, 'steganography.html', {'mode': 'hide'})

# STATIC VIEWS

def welcome(request):
    return render(request, 'welcome.html')

def home_view(request):
    return render(request, 'home.html')

@login_required
def account_view(request):
    return render(request, 'account.html')

def about_view(request):
    return render(request, 'about.html')

@login_required
def stego_image(request):
    return render(request, 'steganography.html')

@login_required
def project_overview(request):
    return render(request, 'project_overview.html')

@login_required
def presentation(request):
    return render(request, 'presentation.html')

@login_required
def poster(request):
    return render(request, 'poster.html')

@login_required
def settings_view(request):
    return render(request, 'settings.html')

@login_required
def admin_dashboard_view(request):
    return render(request, 'admin_dashboard.html')

def build_steps_view(request):
    return render(request, 'build_steps.html')

def demo_mode(request):
    return render(request, 'demo_mode.html')

@login_required
def cyberchef_view(request):
    return render(request, 'cyberchef.html')

@login_required
def cyberchef_local(request):
    return render(request, 'cyberchef.html')

@login_required
def algo_comparison(request):
    # Fetch encryption algorithm data from DB
    algorithms = EncryptionAlgorithm.objects.all()
    algo_data = [
        {
            "name": algo.name,
            "type": algo.algorithm_type,
            "key_size": algo.key_size,
            "strength": algo.strength,
            "use_cases": algo.use_cases,
            "speed": algo.speed,
            "notes": algo.notes
        }
        for algo in algorithms
    ]
    context = {
        'algo_data_json': json.dumps(algo_data)
    }
    return render(request, 'algo_comparison.html', context)

# KEY AND PIN GENERATION

def generate_secure_key(length: int) -> str:
    """Generate a URL-safe base64-encoded secure random key."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode()

def generate_key(request, algorithm):
    if algorithm == "fernet":
        key = Fernet.generate_key().decode()
    elif algorithm == "chacha20":
        # 32 bytes (256 bits) for ChaCha20
        key = generate_secure_key(32)
    elif algorithm == "aes":
        # 32 bytes (256 bits) for AES-GCM
        key = generate_secure_key(32)
    elif algorithm == "rsa":
        rsa_key = RSA.generate(2048)
        key = rsa_key.publickey().export_key().decode()
    else:
        return JsonResponse({"error": "Unsupported algorithm"}, status=400)

    return JsonResponse({"key": key})

def generate_pin():
    return str(uuid.uuid4().int)[:6]

# 404 ERROR PAGE

def handler404(request, exception):
    return render(request, '404.html', status=404)

def docs_view(request):
    return render(request, 'docs.html')

@login_required
def share_email(request):
    try:
        data = json.loads(request.body)
        email = data.get("email")
        link = data.get("link")
        if not email or not link:
            return JsonResponse({"success": False, "error": "Missing fields"})
        send_mail(
            subject="🔐 SecureFileX: Encrypted File Link",
            message=f"You can access the encrypted file here:\n\n{link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})