from django.apps import AppConfig
import os

# Optional: Pre-setup for file uploads directory, watermarking, etc.
class SecurefilexAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'securefilex_app'
    verbose_name = "SecureFileX Application"

    def ready(self):
        # Setup upload folder
        upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        # Optionally, log this or setup watermark engine here
        print(f"[SecureFileX] Upload folder initialized at {upload_folder}")
def ready(self):
    import securfilex_app.signals