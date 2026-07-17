from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import encryption_view, decryption_view
from django.conf.urls.static import static
from .views import verify_pin
urlpatterns = [
    # 🔐 Authentication
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="welcome.html"),
    path('settings/', views.settings_view, name='settings'),

    # 👤 User & Admin Dashboards
    path("profile/", views.profile, name="profile"),
    path("account/", views.account_view, name="account"),
    path("admin-dashboard/", views.admin_dashboard_view, name="admin_dashboard"),
    path("share/email/", views.share_email, name="share_email"),
    

    # 🌐 Public Pages
    path("", views.welcome, name="welcome"),
    path("home/", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("build-steps/", views.build_steps_view, name="build_steps"),
    path("demo/", views.demo_mode, name="demo_mode"),
    path('presentation-poster/', views.project_overview, name='project_overview'),
    path('presentation/', views.presentation, name='presentation'),
    path('poster/', views.poster, name='poster'),

    # 🔐 File Encryption / Decryption
    path('encrypt/', views.encryption_view, name='encrypt'),
    path('decrypt/', views.decryption_view, name='decrypt'),
    path('encrypt/', views.encryption_view, name='encrypt'),
    path('encrypt/', encryption_view, name='encrypt'),
    path('decrypt/', decryption_view, name='decrypt'),
    path('encrypt/', views.encrypt_file, name='encrypt_file'),
    path('decrypt/', views.decrypt_file, name='decrypt_file'),
    path('decrypt/', views.decryption_view, name='decryption'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('generate-key/<str:algorithm>/', views.generate_key, name='generate_key'),
    path('verify/<str:filename>/<str:pin>/', verify_pin, name='verify_pin'),


    # 🧪 CyberChef
    path("cyberchef/", views.cyberchef_view, name="cyberchef_view"),
    path("cyberchef-local/", views.cyberchef_local, name="cyberchef"),

    # 🖼️ Steganography
    path("steganography/", views.steganography_view, name="steganography"),
    path('share/', views.share, name='share'),
    path('steganography/', views.steganography_view, name='steganography'),

    # 📁 Download & Results
    path("download/<str:filename>/", views.download_file, name="download"),
    path('download-decrypted-file/<str:filename>/', views.download_file, name='download_decrypted_file'),
    path('result/', views.result, name='result'), 
    path('verify/<str:filename>/<str:pin>/', views.verify_pin, name='verify'),
    path('verify/<str:filename>/<str:pin>/', views.verify_pin, name='verify'),



    # 🤖 Gemini AI Chat
    path("algo-comparison/", views.algo_comparison, name="algo_comparison"),
    path('docs/', views.docs_view, name='docs'),

    # 🔁 Password Reset (Django built-in views)
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
]
