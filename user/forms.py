from django.contrib.auth.forms import UserCreationForm
from django.forms import ModelForm

from .models import Customer


class CustomerCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Customer
        fields = UserCreationForm.Meta.fields + (
            "name",
            "email",
            "phone_number",
            "address",
        )


class CustomerUpdateForm(ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "email", "phone_number", "address"]
