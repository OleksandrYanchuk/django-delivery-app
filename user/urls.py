from django.urls import path

from .views import (
    index,
    CustomerDetailView,
    CustomerCreateView,
    CustomerDeleteView,
    CustomerUpdateView,
)


urlpatterns = [
    path("", index, name="index"),
    path("customer/<int:pk>/", CustomerDetailView.as_view(), name="customer-detail"),
    path(
        "customer/<int:pk>/update/",
        CustomerUpdateView.as_view(),
        name="customer-update",
    ),
    path("customer/create/", CustomerCreateView.as_view(), name="customer-create"),
    path(
        "customer/<int:pk>/delete/",
        CustomerDeleteView.as_view(),
        name="customer-delete",
    ),
]

app_name = "user"
