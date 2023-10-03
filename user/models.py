import logging

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_save
from django.dispatch import receiver

from django.urls import reverse
from geopy import Nominatim


logger = logging.getLogger(__name__)


class Customer(AbstractUser):
    name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=14)
    address = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    user_lat = models.FloatField(null=True, blank=True)
    user_lng = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def get_absolute_url(self):
        return reverse("user:customer-detail", kwargs={"pk": self.pk})


@receiver(pre_save, sender=Customer)
def update_customer_coordinates(sender, instance, **kwargs):
    geolocator = Nominatim(user_agent="myGeocoder")
    if instance.address:
        parts = instance.address.split(",")
        # Перевірити, чи останнє слово є числом з довжиною 5 (поштовий індекс)
        last_word = parts[-1].strip()
        if last_word.isdigit() and len(last_word) == 5:
            # Якщо останнє слово - це поштовий індекс, видалити його
            new_address = ", ".join(parts[:-1])
        else:
            # Якщо останнє слово не є поштовим індексом, залишити адресу без змін
            new_address = instance.address

        location = geolocator.geocode(new_address)

        if location:
            instance.user_lat = location.latitude
            instance.user_lng = location.longitude
