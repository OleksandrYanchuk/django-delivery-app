from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponse,
    HttpRequest,
)
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render
from geopy import Nominatim

from .forms import CustomerCreationForm
from .models import Customer


@login_required
def index(request: HttpRequest) -> HttpResponse:
    """View function for the home page of the site."""
    num_customers: int = Customer.objects.count()
    num_visits: int = request.session.get("num_visits", 0)
    request.session["num_visits"] = num_visits + 1

    context = {
        "num_customers": num_customers,
        "num_visits": num_visits + 1,
    }

    return render(request, "user/index.html", context=context)


@login_required
def user_details(request) -> HttpResponseRedirect:
    """View function to handle user details based on their role."""
    user = request.user
    return HttpResponseRedirect(f"/customer/{user.pk}")


class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    permission_required = "user.change_own_master"
    model = Customer
    form_class = CustomerCreationForm
    success_url = reverse_lazy("delivery_service:customer-list")
    template_name = "delivery_service/customer_update_form.html"

    def test_func(self) -> bool:
        """
        Checks if the user has permission to update the customer details.
        Returns True if the user matches the customer's user, False otherwise.
        """
        return self.request.user == self.get_object().user

    def handle_no_permission(self) -> HttpResponse:
        """
        Handles the case when the user does not have permission to update the customer details.
        Returns an HTTP Forbidden response with a rendered template for 403 error.
        """
        return HttpResponseForbidden(
            render_to_string(
                "nail_service/403.html",
                {"error_message": self.get_permission_denied_message()},
            )
        )


class CustomerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Customer
    queryset = Customer.objects.all()


class CustomerCreateView(generic.CreateView):
    model = Customer
    form_class = CustomerCreationForm
    success_url = reverse_lazy("nail_service:customer-list")


class CustomerDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Customer
    success_url = reverse_lazy("nail_service:customer-list")

    def test_func(self) -> bool:
        """
        Checks if the user has permission to delete the customer.
        Returns True if the user matches the customer's user, False otherwise.
        """
        return self.request.user == self.get_object().user

    def handle_no_permission(self) -> HttpResponse:
        """
        Handles the case when the user does not have permission to delete the customer.
        Returns an HTTP Forbidden response with a rendered template for 403 error.
        """
        return HttpResponseForbidden(
            render_to_string(
                "nail_service/403.html",
                {"error_message": self.get_permission_denied_message()},
            )
        )
