from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="myauth_profile")  # <--- related_name
    last_seen = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.user.username


