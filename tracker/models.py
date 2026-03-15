from django.db import models

# Create your models here.
from django.db import models


class Package(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tracking_code = models.CharField(max_length=100, unique=True)
    company = models.CharField(max_length=100)