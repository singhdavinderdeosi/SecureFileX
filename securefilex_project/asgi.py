import os
import django
from channels.routing import get_default_application
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securefilex_project.settings')

# Load Django
django.setup()

# Optional: Use Channels routing if WebSockets are integrated
# If no Channels setup yet, default to HTTP ASGI app
try:
    from securefilex_project.routing import application as channels_application
    application = channels_application
except ImportError:
    application = get_asgi_application()
