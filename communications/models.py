from django.db import models
from profiles.models import Profile


class Message(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now=True)

