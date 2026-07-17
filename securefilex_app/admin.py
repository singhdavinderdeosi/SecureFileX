from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile

# 👤 User Profile & Roles with Avatar
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'image_preview')
    list_filter = ('role',)
    search_fields = ('user__username',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Avatar'
