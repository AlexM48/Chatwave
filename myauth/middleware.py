from django.utils import timezone
from mychat.models import UserProfile

class UpdateLastSeenMiddleware:
    """
    Обновляет поле last_seen для текущего пользователя при каждом запросе.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Создаём профиль пользователя, если его нет
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.last_seen = timezone.now()
            profile.save(update_fields=['last_seen'])

        return response
