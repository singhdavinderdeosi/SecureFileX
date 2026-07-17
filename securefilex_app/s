import os
import mimetypes
from PIL import Image
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, FileResponse, JsonResponse, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .utils import generate_ai_key
from .models import FileMetadata, ActivityLog

# ✅ Use encryption and decryption from standalone modules
from .encryption.encryption import encrypt_file, save_metadata, generate_otp, send_otp
from .decryption import decrypt_file, verify_otp_and_get_metadata

# ✅ Keep AI and steganography from utils if still used
from .utils import (
    gemini_api,
    log_activity,
    get_file_metadata,
    encode_image_steganography,
    decode_image_steganography,
)

BASE_DIR = settings.MEDIA_ROOT

# ------------------------------
# ✅ AUTHENTICATION VIEWS
# ------------------------------

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
            if user.is_superuser:
                return redirect("admin_dashboard")
            return redirect("profile")
        messages.error(request, "Invalid username or password.")
    return render(request, "registration/login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("welcome")

# ------------------------------
# ✅ USER DASHBOARD
# ------------------------------

@login_required
def profile(request):
    return render(request, 'account.html')

# ------------------------------
# ✅ ADMIN DASHBOARD & BULK ROLE CONTROL
# ------------------------------

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    if request.method == "POST":
        user_ids = request.POST.getlist("user_ids")
        action = request.POST.get("bulk_action")

        if action not in ["promote", "demote"]:
            messages.error(request, "Invalid action.")
            return redirect("admin_dashboard")

        for uid in user_ids:
            try:
                user = User.objects.get(pk=uid)
                if user != request.user and not user.is_superuser:
                    user.is_staff = (action == "promote")
                    user.save()
            except User.DoesNotExist:
                continue

        messages.success(request, "✅ Bulk action completed.")
        return redirect("admin_dashboard")

    users = User.objects.exclude(id=request.user.id).order_by('username')
    return render(request, "admin_dashboard.html", {"users": users})

# ------------------------------
# ✅ HOME / WELCOME PAGE
# ------------------------------

def dashboard(request):
    return render(request, 'welcome.html')


# ------------------------------
# ✅ FILE ENCRYPTION VIEW
# ------------------------------

@login_required
def encryption_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        algorithm = request.POST.get('algorithm')
        share_with = request.POST.get('share_with_email')  # Optional field for sharing
        user_key = request.POST.get('password')  # Can be left empty for auto-generation

        if not uploaded_file or not algorithm:
            messages.error(request, "File and algorithm are required.")
            return redirect('encrypt')

        try:
            # Auto-generate key if not provided
            generated_key = None
            if not user_key:
                user_key = generate_ai_key()
                generated_key = user_key

            # Encrypt file
            encrypted_file, otp = encrypt_file(
                file=uploaded_file,
                algorithm=algorithm,
                user=request.user,
                password=user_key,
                share_with=share_with
            )

            # Save encrypted file and generate URL
            file_urls = [save_encrypted_file(encrypted_file, request.user)]

            # AI suggestion (optional logic)
            suggestion = generate_ai_suggestion(algorithm)

            messages.success(request, f"File encrypted successfully! OTP: {otp}")

            return render(request, 'encrypt.html', {
                'file_urls': file_urls,
                'suggestion': suggestion,
                'generated_key': generated_key  # Only shown if it was auto-generated
            })

        except Exception as e:
            messages.error(request, f"Encryption failed: {str(e)}")
            return redirect('encrypt')

    return render(request, 'encrypt.html')

# ------------------------------
# ✅ FILE DECRYPTION VIEW
# ------------------------------

@login_required
def decryption_view(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        otp = request.POST.get('otp')

        if not filename or not otp:
            messages.error(request, "Filename and OTP are required.")
            return redirect('decrypt')

        try:
            decrypted_file = decrypt_file(user=request.user, filename=filename, otp=otp)
            messages.success(request, f"File decrypted successfully!")
            return FileResponse(decrypted_file, as_attachment=True)
        except Exception as e:
            messages.error(request, f"Decryption failed: {str(e)}")
            return redirect('decrypt')

    return render(request, 'decrypt.html')

# ------------------------------
# ✅ FILE SHARING / OTP VIEW
# ------------------------------

@login_required
def share_file_view(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        algorithm = request.POST.get('algorithm')

        try:
            metadata = get_file_metadata(request.user, filename, algorithm)
            otp = generate_and_send_otp(request.user, metadata)
            messages.success(request, f"OTP for '{filename}' has been sent: {otp}")
        except Exception as e:
            messages.error(request, f"OTP sharing failed: {str(e)}")

    return render(request, 'share.html')


# ------------------------------
# ✅ SECURE FILE DOWNLOAD VIEW
# ------------------------------

@login_required
def download_file(request, filename):
    user_folder = os.path.join(BASE_DIR, 'media', 'encrypted', request.user.username)
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        raise Http404("Requested file not found.")

    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or 'application/octet-stream'

    return FileResponse(open(file_path, 'rb'), content_type=mime_type, as_attachment=True, filename=filename)


# ------------------------------
# ✅ ACTIVITY LOG VIEW
# ------------------------------

@login_required
def logs_view(request):
    logs = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'logs.html', {'logs': logs})


# ------------------------------
# ✅ IMAGE STEGANOGRAPHY VIEW
# ------------------------------

@login_required
def image_steganography_view(request):
    if request.method == 'POST':
        uploaded_image = request.FILES.get('image')
        message = request.POST.get('message')
        action = request.POST.get('action')  # "hide" or "extract"

        if not uploaded_image:
            messages.error(request, "Please upload an image.")
            return redirect('image_steganography')

        user_folder = os.path.join(settings.MEDIA_ROOT, request.user.username)
        os.makedirs(user_folder, exist_ok=True)

        image_path = os.path.join(user_folder, uploaded_image.name)
        with open(image_path, 'wb') as f:
            for chunk in uploaded_image.chunks():
                f.write(chunk)

        try:
            if action == 'hide' and message:
                output_path = os.path.join(user_folder, f'stego_{uploaded_image.name}')
                hide_message_in_image(image_path, message, output_path)

                log_user_activity(request.user, f"Message hidden in image '{uploaded_image.name}'")
                return FileResponse(open(output_path, 'rb'), as_attachment=True)

            elif action == 'extract':
                extracted_msg = extract_message_from_image(image_path)
                log_user_activity(request.user, f"Message extracted from image '{uploaded_image.name}'")
                return render(request, 'image_steganography.html', {'extracted_message': extracted_msg})

            else:
                messages.error(request, "Invalid action or missing message.")

        except Exception as e:
            messages.error(request, f"Steganography operation failed: {str(e)}")

    return render(request, 'image_steganography.html')


# ------------------------------
# ✅ SUGGEST ENCRYPTION KEY VIEW
# ------------------------------

@login_required
def suggest_encryption_key(request):
    if request.method == 'POST':
        description = request.POST.get('description')

        prompt = f"""You are a cybersecurity expert.
        Suggest a highly secure key or passphrase for encrypting a file.
        File description: {description}"""

        suggestion = gemini_api(prompt, session_id=request.user.username)
        return JsonResponse({'suggestion': suggestion})


# ------------------------------
# ✅ GEMINI CHAT VIEW
# ------------------------------

@csrf_exempt
def gemini_chat_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        prompt = data.get("prompt")
        response = gemini_api(prompt)
        return JsonResponse({'response': response})

# ------------------------------
# ADMIN DASHBOARD VIEW
# ------------------------------

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard_view(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    recent_logs = ActivityLog.objects.order_by('-timestamp')[:10]
    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'active_users': active_users,
        'recent_logs': recent_logs,
    })

# ------------------------------
# BULK USER ROLE UPDATE VIEW
# ------------------------------

@login_required
@user_passes_test(lambda u: u.is_superuser)
def bulk_user_role_update(request):
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        role = request.POST.get('role')

        if not user_ids or not role:
            messages.error(request, "Please select users and a role.")
            return redirect('bulk_user_role_update')

        try:
            with transaction.atomic():
                for user_id in user_ids:
                    user = User.objects.get(id=user_id)
                    user.groups.clear()
                    group, _ = Group.objects.get_or_create(name=role)
                    user.groups.add(group)
            messages.success(request, "User roles updated successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    users = User.objects.all()
    groups = Group.objects.all()
    return render(request, 'bulk_user_role_update.html', {'users': users, 'groups': groups})


# ------------------------------
# ADMIN DASHBOARD VIEW
# ------------------------------

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard_view(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    recent_logs = ActivityLog.objects.order_by('-timestamp')[:10]
    return render(request, 'admin_dashboard.html', {
        'total_users': total_users,
        'active_users': active_users,
        'recent_logs': recent_logs,
    })


# ------------------------------
# BULK USER ROLE UPDATE VIEW
# ------------------------------

@login_required
@user_passes_test(lambda u: u.is_superuser)
def bulk_user_role_update(request):
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        role = request.POST.get('role')

        if not user_ids or not role:
            messages.error(request, "Please select users and a role.")
            return redirect('bulk_user_role_update')

        try:
            with transaction.atomic():
                for user_id in user_ids:
                    user = User.objects.get(id=user_id)
                    user.groups.clear()
                    group, _ = Group.objects.get_or_create(name=role)
                    user.groups.add(group)
            messages.success(request, "User roles updated successfully.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    users = User.objects.all()
    groups = Group.objects.all()
    return render(request, 'bulk_user_role_update.html', {'users': users, 'groups': groups})


# ------------------------------
# ADMIN CONFIGURATION VIEWS
# ------------------------------

@user_passes_test(lambda u: u.is_superuser)
def admin_config(request):
    return render(request, 'admin_config.html')


@user_passes_test(lambda u: u.is_superuser)
def admin_logs(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')[:100]
    return render(request, 'admin_logs.html', {'logs': logs})


@user_passes_test(lambda u: u.is_superuser)
def admin_encryption(request):
    files = FileMetadata.objects.all().order_by('-timestamp')
    return render(request, 'admin_encryption.html', {'files': files})


@user_passes_test(lambda u: u.is_superuser)
def admin_permissions(request):
    users = User.objects.exclude(is_superuser=True)

    if request.method == "POST":
        for user in users:
            role = request.POST.get(f'role_{user.id}')
            user.is_staff = (role == 'staff')
            user.save()
        messages.success(request, "Permissions updated successfully.")
        return redirect('admin_permissions')

    return render(request, 'admin_permissions.html', {'users': users})


@user_passes_test(lambda u: u.is_superuser)
def change_user_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_staff = not user.is_staff
    user.save()
    messages.success(request, f"{user.username}'s role has been updated.")
    return redirect('admin_permissions')


@user_passes_test(lambda u: u.is_superuser)
@require_POST
def bulk_change_user_role(request):
    user_ids = request.POST.getlist('user_ids')
    action = request.POST.get('action')

    if action not in ['promote', 'demote']:
        messages.error(request, 'Invalid action specified.')
        return redirect('admin_permissions')

    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            user.is_staff = (action == 'promote')
            user.save()
        except User.DoesNotExist:
            continue

    messages.success(request, 'User roles updated successfully.')
    return redirect('admin_permissions')


# ------------------------------
# BASIC ROUTES
# ------------------------------

def welcome(request):
    return render(request, 'welcome.html')


def home_view(request):
    return render(request, 'home.html')


@login_required
def account_view(request):
    return render(request, 'account.html')


def about_view(request):
    return render(request, 'about.html')


def build_steps_view(request):
    return render(request, 'build_steps.html')


def demo_mode(request):
    return render(request, 'demo.html')


@login_required
def cyberchef_view(request):
    return render(request, 'cyberchef.html')


@login_required
def cyberchef_local(request):
    return render(request, 'cyberchef_local.html')


# ------------------------------
# FEATURE & TOOL PAGES
# ------------------------------

@login_required
def stego_image(request):
    return render(request, 'steganography.html')


@login_required
def ai_suggestions(request):
    return render(request, 'ai_suggestions.html')


@login_required
def key_management(request):
    return render(request, 'key_vault.html')


@login_required
def download(request, filename):
    return render(request, 'download.html', {'filename': filename})


@login_required
def result_view(request):
    return render(request, 'result.html')


@login_required
def gemini_chat_api(request):
    return render(request, 'gemini_chat.html')


def algo_comparison(request):
    return render(request, 'algo_comparison.html')


# ------------------------------
# EXPORT LOGS VIEW
# ------------------------------

@user_passes_test(lambda u: u.is_superuser)
def export_logs(request, format):
    logs = ActivityLog.objects.all()

    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Action', 'Timestamp', 'Details'])

        for log in logs:
            writer.writerow([
                log.user.username if log.user else 'Anonymous',
                log.action,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.details
            ])
        return response

    elif format == 'json':
        data = [{
            'user': log.user.username if log.user else 'Anonymous',
            'action': log.action,
            'timestamp': log.timestamp.isoformat(),
            'details': log.details
        } for log in logs]
        return HttpResponse(json.dumps(data, indent=4), content_type='application/json')

    return HttpResponse("Invalid format. Use 'csv' or 'json'.", status=400)
