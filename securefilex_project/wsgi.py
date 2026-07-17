import os
from django.core.wsgi import get_wsgi_application

# 🔐 Set the environment to point to your Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securefilex_project.settings')

# 🌐 Get the WSGI application for serving your app
application = get_wsgi_application()
