from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    course = models.CharField(max_length=100)


class ConnectionState(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    connection_id = models.CharField(max_length=255)
    revocation_registry_id = models.CharField(max_length=255)
    revocation_id = models.CharField(max_length=255)
    presentation_exchange_id = models.CharField(max_length=255)
    state = models.CharField(max_length=50, default="NEW")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.state}"
