from django.db import models
from django.contrib.auth.models import AbstractUser

class Profile(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    email = models.CharField(max_length=255, unique=True,null=True)
    password = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    profile = models.ForeignKey(Profile, on_delete=models.DO_NOTHING, blank=True, null=True)
    photo_url = models.ImageField(upload_to='photos/', blank=True, null=True)

    REQUIRED_FIELDS = []