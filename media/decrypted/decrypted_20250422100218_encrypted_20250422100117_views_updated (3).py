
import os
import json
import base64
import logging
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from openai import OpenAI

from .encryption.encryption import (
    encrypt_data,
    derive_key_from_passphrase,
    save_key_entry,
    generate_fernet_key,
    generate_aes_key,
    generate_random_passphrase,
    hide_text_in_image,
    extract_text_from_image,
    hash_md5,
    hash_sha256,
    bcrypt_hash,
    bcrypt_verify
)

from .encryption.decryption import decrypt_data

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), '../securefilex.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@login_required
def index(request):
    context = {"message": "", "generated_key": "", "download_url": "", "salt": ""}
    if request.method == "POST":
        file = request.FILES.get("file")
        key = request.POST.get("key", "").strip()
        algo = request.POST.get("algorithm", "")
        is_passphrase = request.POST.get("use_passphrase") == "on"

        if file and algo:
            try:
                data = file.read()
                if not key and algo == "Fernet (AES)" and not is_passphrase:
                    key = generate_fernet_key()

                encrypted, final_key, salt = encrypt_data(data, key, algo, is_passphrase)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"encrypted_{timestamp}_{file.name}"
                path = os.path.join("encrypted", filename)
                full_path = os.path.join(settings.MEDIA_ROOT, path)

                default_storage.save(full_path, ContentFile(encrypted))
                save_key_entry(filename, algo, final_key, salt)
                logging.info(f"Encrypted: {file.name} using {algo}")

                context.update({
                    "message": "✅ File encrypted successfully.",
                    "generated_key": final_key,
                    "download_url": f"/media/{path}",
                    "salt": salt
                })
            except Exception as e:
                context["message"] = f"❌ Encryption failed: {str(e)}"
    return render(request, "encrypt.html", context)

@login_required
def decrypt(request):
    context = {"message": "", "decrypted_file_url": ""}
    if request.method == "POST":
        file = request.FILES.get("file")
        key = request.POST.get("key", "").strip()
        salt = request.POST.get("salt", "").strip()
        algo = request.POST.get("algorithm", "")
        is_passphrase = request.POST.get("use_passphrase") == "on"

        if file and key and algo:
            try:
                decrypted = decrypt_data(file.read(), key, algo, salt, is_passphrase)
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"decrypted_{timestamp}_{file.name.replace('.encrypted', '')}"
                path = os.path.join("decrypted", filename)
                full_path = os.path.join(settings.MEDIA_ROOT, path)

                default_storage.save(full_path, ContentFile(decrypted))
                logging.info(f"Decrypted: {file.name} using {algo}")

                context.update({
                    "message": "✅ File decrypted successfully.",
                    "decrypted_file_url": f"/media/{path}"
                })
            except Exception as e:
                context["message"] = f"❌ Decryption failed: {str(e)}"
    return render(request, "decrypt.html", context)

@login_required
def download(request, filename):
    path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(path):
        return FileResponse(open(path, 'rb'), as_attachment=True)
    raise Http404("File not found")

@login_required
def log_chart(request):
    log_path = os.path.join(settings.BASE_DIR, "securefilex.log")
    if not os.path.exists(log_path):
        return HttpResponse("No logs available", content_type="text/plain")

    with open(log_path) as f:
        lines = f.readlines()

    algos = ["Fernet (AES)", "ChaCha20", "RSA", "AES (PyCryptodome)"]
    counts = {algo: 0 for algo in algos}
    for line in lines:
        for algo in algos:
            if algo in line:
                counts[algo] += 1

    if sum(counts.values()) == 0:
        return HttpResponse("⚠️ No encryption activity found.", content_type="text/plain")

    fig, ax = plt.subplots()
    ax.pie(counts.values(), labels=counts.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')

    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.read(), content_type='image/png')

@login_required
def logs_dashboard(request):
    log_path = os.path.join(settings.BASE_DIR, "securefilex.log")
    logs, summary = "", ""

    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            logs = f.read()

        try:
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes encryption logs."},
                    {"role": "user", "content": f"Summarize the following SecureFileX logs:\n{logs}"}
                ]
            )
            summary = res.choices[0].message.content
        except Exception as e:
            summary = f"⚠️ AI summary failed: {str(e)}"

    new_log_count = logs.count("Encrypted:")
    ai_count = 1 if summary else 0
    user_count = 1250
    new_user_count = 108

    cards = [
        {"label": "New Logs", "count": new_log_count, "color": "primary", "icon": "fa-file-alt", "trend": "+12% this week"},
        {"label": "Unique Users", "count": user_count, "color": "success", "icon": "fa-user-shield", "trend": "+17% in 7d"},
        {"label": "AI Summaries", "count": ai_count, "color": "warning", "icon": "fa-brain", "trend": "Auto generated"},
        {"label": "New Users", "count": new_user_count, "color": "danger", "icon": "fa-user-plus", "trend": "-12% this week"},
    ]

    return render(request, "logs.html", {
        "logs": logs,
        "ai_summary": summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "cards": cards,
    })

@login_required
def download_logs(request):
    path = os.path.join(settings.BASE_DIR, "securefilex.log")
    if os.path.exists(path):
        return FileResponse(open(path, 'rb'), as_attachment=True)
    raise Http404("Log file not found.")

@login_required
def account_view(request):
    if request.method == "POST" and request.FILES.get("profile_image"):
        profile_image = request.FILES["profile_image"]
        path = f"profile_pics/{request.user.username}.png"
        full_path = os.path.join(settings.MEDIA_ROOT, path)
        default_storage.save(full_path, ContentFile(profile_image.read()))
        messages.success(request, "✅ Avatar updated successfully.")
    return render(request, "account.html")

def welcome_view(request):
    return render(request, "welcome.html")

def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")

def build_steps_view(request):
    return render(request, "build_steps.html")

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "✅ Account created successfully!")
        return redirect("login")
    elif request.method == "POST":
        messages.error(request, "❌ Please correct the errors below.")
    return render(request, "registration/signup.html", {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "✅ Welcome back!")
        return redirect("home")
    elif request.method == "POST":
        messages.error(request, "❌ Invalid credentials.")
    return render(request, "registration/login.html", {'form': form})
