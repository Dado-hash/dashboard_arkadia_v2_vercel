from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from funds_and_strategies.models import Fund

class CustomUser(AbstractUser):
    is_privileged = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username