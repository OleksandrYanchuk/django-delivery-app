from django.db import models
from django.contrib.auth.models import AbstractUser

from django.urls import reverse


class Customer(AbstractUser):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=14)
    address = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def get_absolute_url(self):
        return reverse("user:customer-detail", kwargs={"pk": self.pk})
