from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .validators import validate_file_size

class ChatRoom(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(User, related_name="accessible_rooms", blank=True)

    def __str__(self):
        return self.name

    # Проверка доступа пользователя
    def user_has_access(self, user):
        if not self.is_locked:
            return True
        return user in self.allowed_users.all() or user.is_staff or user.is_superuser

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    video = models.FileField(upload_to='chat_videos/', blank=True, null=True, validators=[validate_file_size])
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True, validators=[validate_file_size])

    def __str__(self):
        return f'{self.user.username}: {self.content[:20]}'

    # Для WebSocket сериализации
    def as_dict(self):
        return {
            'id': self.id,
            'username': self.user.username,
            'content': self.content,
            'video_url': self.video.url if self.video else None,
            'image_url': self.image.url if self.image else None,
            'is_superuser': self.user.is_superuser,
            'created_at': self.created_at.isoformat()
        }

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mychat_profile")
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.save()
