from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

# ============================
# 🔐 Encryption Algorithm Choices
# ============================

ALGORITHM_CHOICES = [
    ('AES-GCM', 'AES-GCM'),
    ('ChaCha20', 'ChaCha20'),
    ('RSA', 'RSA'),
]

# ============================
# 📤 Multi-File Encryption Form (Simplified)
# ============================

class UploadFilesBatchForm(forms.Form):
    files = forms.FileField(
        label='Select files',
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        required=True
    )
    algorithm = forms.ChoiceField(
        choices=ALGORITHM_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    passphrase = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: Enter passphrase (min 8 characters)'
        })
    )
    salt = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: Enter salt'
        })
    )

    def clean_passphrase(self):
        passphrase = self.cleaned_data.get('passphrase')
        if passphrase and len(passphrase) < 8:
            raise ValidationError("Passphrase must be at least 8 characters.")
        return passphrase

# ============================
# 📝 User Registration Form
# ============================

class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repeat password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("⚠️ This email is already in use.")
        return email

class SteganographyForm(forms.Form):
    mode = forms.CharField(widget=forms.HiddenInput())
    image = forms.ImageField(required=False)
    stego_image = forms.ImageField(required=False)
    message = forms.CharField(widget=forms.Textarea, required=False)