from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 🔐 File Metadata for Encryption/Decryption
class FileMetadata(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    key = models.BinaryField()  # Raw or encrypted key
    algorithm = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} - {self.user.username} ({self.algorithm})"

# 📋 Activity Logs for Encryption/Decryption
class ActivityLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)  # Encrypt or Decrypt
    file_name = models.CharField(max_length=255)
    algorithm = models.CharField(max_length=100)
    result = models.TextField(blank=True)

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M:%S} | {self.user.username} | {self.action_type} | {self.algorithm}"

# 👤 User Profile (Optional)
def user_avatar_path(instance, filename):
    return f'avatars/user_{instance.user.id}/{filename}'

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('power', 'Power User'),
        ('regular', 'Regular User'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='regular')
    image = models.ImageField(upload_to=user_avatar_path, default='avatars/default.png', blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'


class EncryptionAlgorithm(models.Model):
    name = models.CharField(max_length=100)
    algorithm_type = models.CharField(max_length=50)
    key_size = models.CharField(max_length=50)
    strength = models.CharField(max_length=50)
    use_cases = models.TextField()
    speed = models.CharField(max_length=50)
    notes = models.TextField()

    def __str__(self):
        return self.name

class PublicDownload(models.Model):
    short_id = models.CharField(max_length=12, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    encrypted_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Optional expiration
    qr_code_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.short_id} → {self.encrypted_filename}"