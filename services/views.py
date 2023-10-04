import requests
from django.http import JsonResponse


import logging
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import (
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseBadRequest,
    HttpResponse,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView
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


class ShopListView(ListView):
    model = Shop
    template_name = "shop/shop_list.html"
    context_object_name = "shop_list"


class ShopDetailView(DetailView):
    model = Shop
    template_name = "shop/shop_detail.html"
    context_object_name = "shop"


class CreateShopView(CreateView):
    model = Shop
    form_class = ShopForm
    template_name = "create_shop.html"
    success_url = reverse_lazy("shop_list")


# Аналогічно, додайте класи для Goods, ShoppingCart і CartItem


class GoodsListView(ListView):
    model = Goods
    template_name = "goods_list.html"
    context_object_name = "goods"


class CreateGoodsView(CreateView):
    model = Goods
    form_class = GoodsForm
    template_name = "create_goods.html"
    success_url = reverse_lazy("goods_list")


class ShoppingCartView(CreateView):
    model = ShoppingCart
    form_class = ShoppingCartForm
    template_name = "shopping_cart/shopping_cart.html"
    success_url = reverse_lazy("shopping_cart")


class ShoppingCartDetailView(DetailView):
    model = ShoppingCart
    template_name = "shopping_cart_detail.html"
    context_object_name = "shopping_cart_detail"


class CartItemView(CreateView):
    model = CartItem
    form_class = CartItemForm
    template_name = "cart_item.html"
    success_url = reverse_lazy("cart_item")

    def total_price_with_discount(self):
        return self.quantity * (
            self.goods.price - (self.goods.price * self.discount_percentage / 100)
        )


class CartItemDetailView(DetailView):
    model = CartItem
    template_name = "cart_item_detail.html"
    context_object_name = "cart_item_detail"


class ShopGoodsDetailView(DetailView):
    model = Shop
    template_name = "shop/shop_goods_detail.html"
    context_object_name = "shop"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shop = self.get_object()  # Отримуємо об'єкт магазину
        goods = Goods.objects.filter(shop_name=shop)  # Фільтруємо товари за магазином
        context["goods"] = goods  # Передаємо список товарів у контекст
        context["shop_list"] = Shop.objects.all()
        return context


@login_required
def add_to_cart(request):
    if request.method == "POST":
        goods_id = request.POST.get("goods", None)
        if goods_id:
            goods = get_object_or_404(Goods, id=goods_id)

            # Перевірка, чи у користувача вже є кошик для покупок
            shopping_cart, created = ShoppingCart.objects.get_or_create(
                user=request.user
            )

            # Перевірка, чи всі товари в кошику належать до одного магазину
            if (
                shopping_cart.goods.filter(shop_name=goods.shop_name).exists()
                or not shopping_cart.goods.all()
            ):
                # Створення нового елемента кошика з товаром і додавання до кошика
                cart_item, created = CartItem.objects.get_or_create(
                    shopping_cart=shopping_cart, goods=goods
                )

                # Якщо товар вже був у кошику, збільшуємо кількість на одиницю
                if not created:
                    cart_item.quantity += 1
                    cart_item.save()

                return HttpResponseRedirect(
                    reverse("services:shop_goods_detail", args=[goods.shop_name.id])
                )
            else:
                # Додайте повідомлення про помилку до контексту
                messages.error(
                    request, "Cannot add items from different shops to the cart"
                )
                return HttpResponseRedirect(reverse("services:shop_goods_detail"))

    # Якщо дані некоректні або HTTP метод GET
    return HttpResponseRedirect(reverse("services:shop_goods_detail"))


def shopping_cart(request):
    # Отримайте кошик поточного користувача
    shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user)

    # Отримайте всі товари у кошику
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
def checkout(request):
    if request.method == "POST":
        recaptcha_token = request.POST.get("recaptchaToken")
        secret_key = "6LcLr2woAAAAAJ2RSZmirteuwzriGjU3Dk8qhtsa"

        # Виконайте запит на сервер reCAPTCHA Enterprise для перевірки
        response = requests.post(
            "https://recaptchaenterprise.googleapis.com/v1beta1/projects/ВАШ_ПРОЕКТ/assessments?key="
            + secret_key,
            json={
                "token": recaptcha_token,
            },
        )

        result = response.json()

        if result["score"] >= 0.5:
            # CAPTCHA пройшла перевірку, тепер ви можете оформити замовлення
            cart_items = CartItem.objects.filter(user=request.user)
            totals = get_totals(cart_items)

            # Оформлення замовлення
            # ...

            # Видаліть всі елементи кошика, пов'язані з поточним користувачем
            cart_items.delete()

            return JsonResponse({"success": True})
        else:
            # CAPTCHA не пройдена
            # Обробіть це відповідним чином і повідомте користувача
            return JsonResponse({"success": False})
    else:
        cart_items = CartItem.objects.filter(user=request.user)
        totals = get_totals(cart_items)
    return render(
        request,
        "shopping_cart/checkout.html",
        {"cart_items": cart_items, "totals": totals},
    )


@login_required
def update_cart_item(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        item_id = request.POST.get("item_id")
        new_quantity = int(request.POST.get("new_quantity", 1))

        # Отримайте об'єкт cart_item за його ідентифікатором item_id
        cart_item = get_object_or_404(CartItem, id=item_id)

        # Оновіть кількість товару
        cart_item.quantity = new_quantity
        cart_item.save()

        # Отримайте оновлену інформацію про товар для повернення на клієнтський бік
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


class OrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    template_name = "order/order_create.html"
    success_url = "/delivery/order-list/"

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.total_amount = 0  # Початкова сума замовлення

        # Створіть номер замовлення на основі поточного часу та дати
        now = timezone.now()
        order_number = f"{now.strftime('%Y%m%d%H%M%S')}_{self.request.user.id}"

        form.instance.order_number = order_number  # Встановіть номер замовлення

        # Отримайте кошик поточного користувача
        shopping_cart, created = ShoppingCart.objects.get_or_create(
            user=self.request.user
        )
        # Retrieve the coupon code from the session if it exists
        coupon_code = self.request.session.get("coupon_code")

        # Отримайте всі товари у кошику
        cart_items = CartItem.objects.filter(shopping_cart=shopping_cart)

        # Обчисліть суму всіх товарів у кошику і встановіть її як total_amount
        total_amount = Decimal("0.00")
        for cart_item in cart_items:
            total_amount += Decimal(str(cart_item.quantity)) * cart_item.goods.price
        print(f"Total Amount: {form.instance.total_amount}")

        form.instance.total_amount = total_amount

        if coupon_code:
            # Perform any additional validation or processing for the coupon
            # Mark the coupon as used
            try:
                coupon = DiscountCoupon.objects.get(code=coupon_code, is_used=False)
                total_with_discount = form.instance.total_amount - (
                    form.instance.total_amount * coupon.discount_percentage / 100
                )
                coupon.is_used = True
                coupon.save()
            except DiscountCoupon.DoesNotExist:
                pass  # Handle the case where the coupon doesn't exist or is already used

        # Збережіть об'єкт Order
        order = form.save()
        if total_with_discount:
            order.total_with_discount = (
                total_with_discount  # You can modify this logic as needed
            )
            order.save()

        # Створіть об'єкти OrderItem для всіх товарів у кошику
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.goods,
                quantity=cart_item.quantity,
            )

        # Видаліть всі елементи кошика, пов'язані з поточним користувачем
        cart_items.delete()

        return super().form_valid(form)


# Class-based view для відображення списку замовлень (order list view)
class OrderListView(ListView):
    model = Order
    template_name = "order/order_list.html"
    context_object_name = (
        "orders"  # Ім'я змінної, яку ви будете використовувати у шаблоні
    )


class OrderDetailView(DetailView):
    model = Order
    template_name = "order/order_detail.html"
    context_object_name = "order"


# Class-based view для редагування/видалення елементу замовлення (order item view)
class OrderItemDetailView(DetailView):
    model = OrderItem
    template_name = "order/order_item_detail.html"
    context_object_name = "order_item"


def update_user_info(request):
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        new_phone_number = request.POST.get("phone_number")
        new_address = request.POST.get("address")

        # Отримайте користувача з об'єкта запиту
        user = request.user

        # Оновіть дані користувача
        user.phone_number = new_phone_number
        user.address = new_address
        user.save()

        return JsonResponse({"success": True})

    return JsonResponse({"message": "Not an AJAX request"}, status=400)


def active_coupons(request):
    user = request.user  # Отримуємо поточного користувача
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


def apply_coupon(request):
    # Отримайте код купона з POST-запиту
    coupon_code = request.POST.get("coupon_code")

    # Отримайте поточного користувача
    user = request.user

    try:
        # Знайдіть купон за кодом і перевірте, чи він активний та належить користувачу
        coupon = DiscountCoupon.objects.get(code=coupon_code, is_used=False, user=user)

        # Отримайте всі товари у кошику користувача
        cart_items = CartItem.objects.filter(shopping_cart__user=user)

        # Перевірте, чи купон відноситься до потрібного магазину
        if all(item.goods.shop_name.id == coupon.shop.id for item in cart_items):
            # Застосуйте знижку до суми замовлення
            discount_amount = apply_discount_coupon(coupon)
            print(f"Discount amount applied: {discount_amount}")

            request.session["coupon_code"] = coupon_code

            # Підготуйте дані для відправки у відповіді
            response_data = {
                "success": True,
                "discount_amount": discount_amount,
            }

            # Виведення інформації у журнал сервера
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


def apply_discount_coupon(coupon):
    # Отримайте всі товари у кошику користувача
    cart_items = CartItem.objects.filter(shopping_cart__user=coupon.user)

    # Обчислення загальної суми всіх товарів у кошику
    totals = get_totals(cart_items)

    # Обчислення знижки за допомогою відсоткового значення
    discount_percentage = Decimal(coupon.discount_percentage) / 100
    discount_amount = sum(totals) - (sum(totals) * discount_percentage)

    # Реалізуйте логіку оновлення замовлення з врахуванням знижки
    # Поверніть суму знижки, щоб відобразити на сторінці
    return discount_amount
