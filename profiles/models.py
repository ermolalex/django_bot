from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator


class Company(models.Model):
    name = models.CharField(max_length=50, unique=True)
    inn = models.IntegerField(unique=True, null=True, blank=True)
    channel_name = models.CharField(max_length=20, unique=True, null=True, blank=True)
    channel_id = models.IntegerField(unique=True, null=True, blank=True)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Profile(AbstractUser):
    phone = models.CharField(max_length=15, unique=True, db_index=True, blank=True, null=True)
    tg_id = models.IntegerField(unique=True, db_index=True, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, blank=True, null=True)


    def get_zulip_topic_name(self):
        return f"{self.first_name}_{self.tg_id}"
