from django.contrib.auth.decorators import login_required
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

from .forms import CustomerCreationForm, CustomerUpdateForm
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
    user = request.user
    return HttpResponseRedirect(f"/customer/{user.pk}")


class CustomerUpdateView(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    permission_required = "user.change_own_master"
    model = Customer
    form_class = CustomerUpdateForm
    success_url = reverse_lazy("user:index")
    template_name = "user/customer_update_form.html"

    def test_func(self) -> bool:
        return self.request.user.pk == self.get_object().pk

    def handle_no_permission(self) -> HttpResponse:
        return HttpResponseForbidden(
            render_to_string(
                "user/403.html",
                {"error_message": self.get_permission_denied_message()},
            )
        )


class CustomerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Customer
    queryset = Customer.objects.all()


class CustomerCreateView(generic.CreateView):
    model = Customer
    form_class = CustomerCreationForm
    success_url = reverse_lazy("user:index")


class CustomerDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Customer
    success_url = reverse_lazy("user:index")

    def test_func(self) -> bool:
        return self.request.user.pk == self.get_object().pk

    def handle_no_permission(self) -> HttpResponse:
        return HttpResponseForbidden(
            render_to_string(
                "user/403.html",
                {"error_message": self.get_permission_denied_message()},
            )
        )
