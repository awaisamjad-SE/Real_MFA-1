from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid


# ---------------------------
# Abstract Base Models
# ---------------------------

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True    

class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()        




try:
    products=products.objects.get(id=1)
except products.DoesNotExist:
    print("No products found with id 1")
        