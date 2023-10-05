import os

import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from dotenv import load_dotenv


import logging
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView
from .models import (
    Shop,
    Goods,
    ShoppingCart,
    CartItem,
    Order,
    OrderItem,
    DiscountCoupon,
)
from .forms import (
    ShopForm,
    GoodsForm,
    ShoppingCartForm,
    CartItemForm,
    OrderForm,
    CreateCouponForm,
)


load_dotenv()


class ShopListView(LoginRequiredMixin, ListView):
    model = Shop
    template_name = "shop/shop_list.html"
    context_object_name = "shop_list"


class ShopDetailView(LoginRequiredMixin, DetailView):
    model = Shop
    template_name = "shop/shop_detail.html"
    context_object_name = "shop"


class CreateShopView(LoginRequiredMixin, CreateView):
    model = Shop
    form_class = ShopForm
    template_name = "create_shop.html"
    success_url = reverse_lazy("shop_list")


class GoodsListView(LoginRequiredMixin, ListView):
    model = Goods
    template_name = "goods_list.html"
    context_object_name = "goods"


class CreateGoodsView(LoginRequiredMixin, CreateView):
    model = Goods
    form_class = GoodsForm
    template_name = "create_goods.html"
    success_url = reverse_lazy("goods_list")


class ShoppingCartView(LoginRequiredMixin, CreateView):
    model = ShoppingCart
    form_class = ShoppingCartForm
    template_name = "shopping_cart/shopping_cart.html"
    success_url = reverse_lazy("shopping_cart")


class ShoppingCartDetailView(LoginRequiredMixin, DetailView):
    model = ShoppingCart
    template_name = "shopping_cart_detail.html"
    context_object_name = "shopping_cart_detail"


class CartItemView(LoginRequiredMixin, CreateView):
    model = CartItem
    form_class = CartItemForm
    template_name = "cart_item.html"
    success_url = reverse_lazy("cart_item")

    def total_price_with_discount(self):
        return self.quantity * (
            self.goods.price - (self.goods.price * self.discount_percentage / 100)
        )


class CartItemDetailView(LoginRequiredMixin, DetailView):
    model = CartItem
    template_name = "cart_item_detail.html"
    context_object_name = "cart_item_detail"


class ShopGoodsDetailView(LoginRequiredMixin, DetailView):
    model = Shop
    template_name = "shop/shop_goods_detail.html"
    context_object_name = "shop"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_object()
        goods = Goods.objects.filter(shop_name=shop)
        context["goods"] = goods
        context["shop_list"] = Shop.objects.all()
        return context


@login_required
def add_to_cart(request):
    if request.method == "POST":
        goods_id = request.POST.get("goods", None)
        if goods_id:
            goods = get_object_or_404(Goods, id=goods_id)

            shopping_cart, created = ShoppingCart.objects.get_or_create(
                user=request.user
            )

            if (
                shopping_cart.goods.filter(shop_name=goods.shop_name).exists()
                or not shopping_cart.goods.all()
            ):
                cart_item, created = CartItem.objects.get_or_create(
                    shopping_cart=shopping_cart, goods=goods
                )

                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

                return HttpResponseRedirect(
                    reverse("services:shop_goods_detail", args=[goods.shop_name.id])
                )
            else:
                messages.error(
                    request, "Cannot add items from different shops to the cart"
                )
                return HttpResponseRedirect(reverse("services:shop_goods_detail"))

    return HttpResponseRedirect(reverse("services:shop_goods_detail"))


@login_required
def shopping_cart(request):
    shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user)

    cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)
    totals = get_totals(cart_items)
    lat = 0
    lng = 0
    for cart_item in cart_items:
        lat = cart_item.goods.shop_name.lat
        lng = cart_item.goods.shop_name.lng

    context = {
        "cart_items": cart_items,
        "totals": totals,
        "name": shopping_cart.user.name,
        "email": shopping_cart.user.email,
        "phone_number": shopping_cart.user.phone_number,
        "address": shopping_cart.user.address,
        "user_lat": shopping_cart.user.user_lat,
        "user_lng": shopping_cart.user.user_lng,
        "lat": lat,
        "lng": lng,
    }

    return render(
        request,
        "shopping_cart/shopping_cart.html",
        context=context,
    )


@login_required
def update_cart_item(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        item_id = request.POST.get("item_id")
        new_quantity = int(request.POST.get("new_quantity", 1))

        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.quantity = new_quantity
        cart_item.save()

        updated_item_html = render_to_string(
            "shopping_cart/shopping_cart.html",
            {"item": cart_item},
        )

        response_data = {"updated_item_html": updated_item_html}
        return JsonResponse(response_data)

    return HttpResponseBadRequest()


@login_required
def remove_cart_item(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        item_id = request.POST.get("item_id")

        cart_item = get_object_or_404(CartItem, id=item_id)
        cart_item.delete()

        return JsonResponse({"success": True})

    return HttpResponseBadRequest()


def get_totals(cart_items):
    totals = [item.quantity * item.goods.price for item in cart_items]
    return totals


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "order/order_create.html"
    success_url = "/delivery/order-list/"

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        # Перевірка reCAPTCHA
        recaptcha_token = self.request.POST.get("recaptcha_token")
        recaptcha_secret_key = os.getenv("CAPTCHA_KEY")
        recaptcha_verify_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_data = {
            "secret": recaptcha_secret_key,
            "response": recaptcha_token,
        }

        recaptcha_response = requests.post(recaptcha_verify_url, data=recaptcha_data)
        recaptcha_result = recaptcha_response.json()

        if not recaptcha_result.get("success"):
            return HttpResponseBadRequest("reCAPTCHA verification failed")
        form.instance.total_amount = 0

        now = timezone.now()
        order_number = f"{now.strftime('%Y%m%d%H%M%S')}_{self.request.user.id}"

        form.instance.order_number = order_number

        shopping_cart, created = ShoppingCart.objects.get_or_create(
            user=self.request.user
        )
        coupon_code = self.request.session.get("coupon_code")

        cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)

        total_amount = Decimal("0.00")
        for cart_item in cart_items:
            total_amount += Decimal(str(cart_item.quantity)) * cart_item.goods.price
        print(f"Total Amount: {form.instance.total_amount}")

        form.instance.total_amount = total_amount
        total_with_discount = total_amount

        if coupon_code:
            try:
                coupon = DiscountCoupon.objects.get(code=coupon_code, is_used=False)
                total_with_discount = form.instance.total_amount - (
                    form.instance.total_amount * coupon.discount_percentage / 100
                )
                coupon.is_used = True
                coupon.save()
            except DiscountCoupon.DoesNotExist:
                pass

        order = form.save()
        if total_with_discount:
            order.total_with_discount = total_with_discount
            order.save()

        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.goods,
                quantity=cart_item.quantity,
            )

        cart_items.delete()

        return super().form_valid(form)


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = "order/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "order/order_detail.html"
    context_object_name = "order"


class OrderItemDetailView(LoginRequiredMixin, DetailView):
    model = OrderItem
    template_name = "order/order_item_detail.html"
    context_object_name = "order_item"


@login_required
def update_user_info(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        new_phone_number = request.POST.get("phone_number")
        new_address = request.POST.get("address")
        user = request.user
        user.phone_number = new_phone_number
        user.address = new_address
        user.save()

        return JsonResponse({"success": True})

    return JsonResponse({"message": "Not an AJAX request"}, status=400)


@login_required
def active_coupons(request):
    user = request.user
    active_coupons = DiscountCoupon.objects.filter(user=user, is_used=False)
    today_coupon_count = DiscountCoupon.get_today_coupon_count(user)

    if request.method == "POST":
        form = CreateCouponForm(request.POST)
        if form.is_valid():
            coupon = DiscountCoupon.create_random_coupon(user)
            if coupon:
                return HttpResponseRedirect("/delivery/generate-coupon/")
            else:
                messages.error(
                    request, "Ви вже вичерпали ліміт на сьогодні для генерації купонів."
                )
    else:
        form = CreateCouponForm()

    return render(
        request,
        "coupon/active_coupons.html",
        {
            "active_coupons": active_coupons,
            "form": form,
            "today_coupon_count": today_coupon_count,
        },
    )


@login_required
def apply_coupon(request):
    coupon_code = request.POST.get("coupon_code")
    user = request.user

    try:
        coupon = DiscountCoupon.objects.get(code=coupon_code, is_used=False, user=user)
        cart_items = CartItem.objects.filter(shopping_cart__user=user)

        if all(item.goods.shop_name.id == coupon.shop.id for item in cart_items):
            discount_amount = apply_discount_coupon(coupon)
            print(f"Discount amount applied: {discount_amount}")

            request.session["coupon_code"] = coupon_code

            response_data = {
                "success": True,
                "discount_amount": discount_amount,
            }
            logging.info(f"Response data: {response_data}")

            return JsonResponse(response_data)

        else:
            print("Coupon does not apply to the shop.")
            messages.error(request, "Замовлення ще не створено")
            return JsonResponse(
                {"success": False, "message": "Coupon does not apply to the shop"}
            )

    except DiscountCoupon.DoesNotExist:
        print("Coupon not found or already used.")
        messages.error(request, "Неправильний код купона або купон вже використаний")
        return JsonResponse(
            {"success": False, "message": "Invalid coupon code or coupon already used"}
        )


@login_required
def apply_discount_coupon(coupon):
    cart_items = CartItem.objects.filter(shopping_cart__user=coupon.user)
    totals = get_totals(cart_items)
    discount_percentage = Decimal(coupon.discount_percentage) / 100
    discount_amount = sum(totals) - (sum(totals) * discount_percentage)
    return discount_amount
