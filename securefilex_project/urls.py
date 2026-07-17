from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.static import static
urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 Social Login & Signup (Google, GitHub) via AllAuth
    path('accounts/', include('allauth.urls')),

    # 🔐 Built-in Auth (password reset/change/login/logout etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # 📂 Your main app routes
    path('', include('securefilex_app.urls')),
]

# 📁 Static & Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
