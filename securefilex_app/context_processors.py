from django.conf import settings

def feedback_email(request):
    return {
        'FEEDBACK_EMAIL': settings.FEEDBACK_EMAIL
    }
